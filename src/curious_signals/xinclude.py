"""Safe XInclude graph validation before passing XML to xmllint."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlsplit

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

XINCLUDE_NS = "http://www.w3.org/2001/XInclude"
XINCLUDE_TAG = f"{{{XINCLUDE_NS}}}include"
LIBXML_ALTERNATE_XINCLUDE_NS = "http://www.w3.org/2003/XInclude"
LIBXML_ALTERNATE_XINCLUDE_TAG = f"{{{LIBXML_ALTERNATE_XINCLUDE_NS}}}include"
XML_BASE = "{http://www.w3.org/XML/1998/namespace}base"
ALLOWED_INCLUDE_DIR = "includes"


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _safe_root(source: Path, allowed_root: Path | None) -> tuple[Path | None, str | None]:
    if source.is_symlink():
        return None, f"{source}: XML root must not be a symlink"
    include_root = allowed_root or (
        source.parent
        if source.parent.name == ALLOWED_INCLUDE_DIR
        else source.parent / ALLOWED_INCLUDE_DIR
    )
    if include_root.is_symlink():
        return None, f"{source}: XInclude root must not be a symlink: {include_root}"
    if include_root.parent.is_symlink():
        return None, f"{source}: XML source root must not be a symlink: {include_root.parent}"
    try:
        source_parent = include_root.parent.resolve(strict=True)
        resolved_root = include_root.resolve(strict=True)
        resolved_source = source.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as error:
        return None, f"{source}: cannot resolve XInclude root: {error}"
    if not resolved_root.is_dir() or not _is_within(resolved_root, source_parent):
        return None, f"{source}: expected safe XInclude directory {include_root}"
    if not (resolved_source.parent == source_parent or _is_within(resolved_source, resolved_root)):
        return None, f"{source}: XML source must stay under the configured source root"
    if _is_within(resolved_source, resolved_root) and (
        symlink := _symlink_component(source, include_root)
    ):
        return None, f"{source}: XInclude path must not contain a symlink: {symlink}"
    return resolved_root, None


def _decoded_path(source: Path, href: str) -> tuple[Path | None, str | None]:
    try:
        parsed = urlsplit(href)
    except ValueError as error:
        return None, f"{source}: invalid XInclude href {href!r}: {error}"
    if parsed.scheme or parsed.netloc:
        return None, f"{source}: XInclude href {href!r} must not use a URL"
    if parsed.query or parsed.fragment:
        return None, f"{source}: XInclude href {href!r} must not contain query or fragment data"
    decoded = unquote(parsed.path)
    include_path = Path(decoded)
    if "\\" in decoded or include_path.is_absolute() or not include_path.parts:
        return None, f"{source}: XInclude href {href!r} must be a relative path"
    if ".." in include_path.parts:
        return None, f"{source}: XInclude href {href!r} must stay under includes/"
    return include_path, None


def _symlink_component(path: Path, include_root: Path) -> Path | None:
    current = path
    while current != include_root:
        if current.is_symlink():
            return current
        if current.parent == current:
            break
        current = current.parent
    return None


def _include_target(
    entry: Path, source: Path, href: str, include_root: Path
) -> tuple[Path | None, str | None]:
    include_path, error = _decoded_path(source, href)
    if error or include_path is None:
        return None, error
    if (
        source == entry
        and not _is_within(entry, include_root)
        and include_path.parts[0] != ALLOWED_INCLUDE_DIR
    ):
        return None, f"{source}: XInclude href {href!r} must be a relative includes/ path"
    candidate = source.parent / include_path
    if symlink := _symlink_component(candidate, include_root):
        return None, f"{source}: XInclude path must not contain a symlink: {symlink}"
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError:
        return None, f"{source}: XInclude target does not exist: {href!r}"
    except (OSError, RuntimeError, ValueError) as error:
        return None, f"{source}: cannot resolve XInclude target {href!r}: {error}"
    if not _is_within(resolved, include_root):
        return None, f"{source}: XInclude href {href!r} must stay under includes/"
    if not resolved.is_file():
        return None, f"{source}: XInclude target is not a file: {href!r}"
    return resolved, None


def _parse(source: Path) -> tuple[ET.Element | None, str | None]:
    try:
        parser = ET.DefusedXMLParser(forbid_dtd=True, forbid_entities=True, forbid_external=True)
        return ET.parse(source, parser=parser).getroot(), None
    except OSError as error:
        return None, f"{source}: cannot read XML file: {error}"
    except DefusedXmlException as error:
        return None, f"{source}: unsafe XML rejected before XInclude expansion: {error}"
    except ET.ParseError as error:
        return None, f"{source}: cannot parse XML before XInclude expansion: {error}"


def _unsupported_namespace_errors(source: Path, root: ET.Element) -> list[str]:
    return [
        f"{source}: unsupported XInclude namespace {LIBXML_ALTERNATE_XINCLUDE_NS!r}"
        for element in root.iter()
        if element.tag == LIBXML_ALTERNATE_XINCLUDE_TAG
    ]


def _validate_document(
    entry: Path,
    source: Path,
    include_root: Path,
    visited: set[Path],
    active: set[Path],
) -> list[str]:
    if source in active:
        return [f"{source}: cyclic XInclude graph is not allowed"]
    if source in visited:
        return []
    root, error = _parse(source)
    if error or root is None:
        return [error] if error else []
    if namespace_errors := _unsupported_namespace_errors(source, root):
        return namespace_errors
    active.add(source)
    errors: list[str] = []
    for element in root.iter():
        if XML_BASE in element.attrib:
            errors.append(f"{source}: xml:base is not allowed before XInclude expansion")
        if element.tag != XINCLUDE_TAG:
            continue
        href = element.attrib.get("href")
        if not href:
            errors.append(f"{source}: XInclude element missing href")
            continue
        if element.attrib.get("parse", "xml") != "xml":
            errors.append(f"{source}: XInclude href {href!r} must use XML parsing")
            continue
        target, target_error = _include_target(entry, source, href, include_root)
        if target_error or target is None:
            if target_error:
                errors.append(target_error)
            continue
        errors.extend(_validate_document(entry, target, include_root, visited, active))
    active.remove(source)
    visited.add(source)
    return errors


def validate_xinclude_paths(
    path: str | Path, *, allowed_root: str | Path | None = None
) -> list[str]:
    """Return XML safety and include-boundary errors for one XML graph."""

    source = Path(path)
    if source.is_symlink():
        return [f"{source}: XML root must not be a symlink"]
    root, parse_error = _parse(source)
    if parse_error:
        return [parse_error]
    if root is None:
        return []
    if namespace_errors := _unsupported_namespace_errors(source, root):
        return namespace_errors
    has_include = any(element.tag == XINCLUDE_TAG for element in root.iter())
    if not has_include:
        return [
            f"{source}: xml:base is not allowed before XInclude expansion"
            for element in root.iter()
            if XML_BASE in element.attrib
        ]
    include_root, root_error = _safe_root(
        source, Path(allowed_root) if allowed_root is not None else None
    )
    if root_error or include_root is None:
        return [root_error] if root_error else []
    try:
        entry = source.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as error:
        return [f"{source}: cannot resolve XML root: {error}"]
    return _validate_document(entry, entry, include_root, set(), set())
