"""Safe XInclude path validation before passing XML to xmllint."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlsplit

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

XINCLUDE_NS = "http://www.w3.org/2001/XInclude"
XINCLUDE_TAG = f"{{{XINCLUDE_NS}}}include"
ALLOWED_INCLUDE_DIR = "includes"


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_href(source: Path, href: str) -> str | None:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc:
        return f"{source}: XInclude href {href!r} must not use a URL"
    if parsed.query or parsed.fragment:
        return f"{source}: XInclude href {href!r} must not contain query or fragment data"
    include_path = Path(unquote(parsed.path))
    invalid_prefix = (
        include_path.is_absolute()
        or not include_path.parts
        or include_path.parts[0] != ALLOWED_INCLUDE_DIR
    )
    if invalid_prefix:
        if ".." in include_path.parts:
            return f"{source}: XInclude href {href!r} must stay under includes/"
        return f"{source}: XInclude href {href!r} must be a relative includes/ path"
    if ".." in include_path.parts:
        return f"{source}: XInclude href {href!r} must stay under includes/"
    allowed_dir = source.parent / ALLOWED_INCLUDE_DIR
    if not allowed_dir.is_dir():
        return f"{source}: expected XInclude directory {allowed_dir}"
    candidate = source.parent / include_path
    if not candidate.exists():
        return f"{source}: XInclude target does not exist: {href!r}"
    allowed_resolved = allowed_dir.resolve(strict=True)
    candidate_resolved = candidate.resolve(strict=True)
    if not _is_within(candidate_resolved, allowed_resolved):
        return f"{source}: XInclude href {href!r} must stay under includes/"
    if not candidate_resolved.is_file():
        return f"{source}: XInclude target is not a file: {href!r}"
    return None


def validate_xinclude_paths(path: str | Path) -> list[str]:
    """Return XInclude URL and path-boundary errors for one XML file."""

    source = Path(path)
    try:
        root = ET.parse(source).getroot()
    except OSError as error:
        return [f"{source}: cannot read XML file: {error}"]
    except DefusedXmlException as error:
        return [f"{source}: unsafe XML rejected before XInclude expansion: {error}"]
    except ET.ParseError as error:
        return [f"{source}: cannot parse XML before XInclude expansion: {error}"]
    errors: list[str] = []
    for element in root.iter():
        if element.tag != XINCLUDE_TAG:
            continue
        href = element.attrib.get("href")
        if not href:
            errors.append(f"{source}: XInclude element missing href")
            continue
        if error := _validate_href(source, href):
            errors.append(error)
    return errors
