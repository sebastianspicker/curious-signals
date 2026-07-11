#!/usr/bin/env python3
"""Validate repository XInclude hrefs before xmllint expands them."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

XINCLUDE_NS = "http://www.w3.org/2001/XInclude"
XINCLUDE_TAG = f"{{{XINCLUDE_NS}}}include"
ALLOWED_INCLUDE_DIR = "includes"


def _include_elements(root: ET.Element) -> list[ET.Element]:
    return [element for element in root.iter() if element.tag == XINCLUDE_TAG]


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_url_boundary(source: Path, href: str) -> str | None:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc:
        return f"{source}: XInclude href {href!r} must not use a URL"
    if parsed.query or parsed.fragment:
        return f"{source}: XInclude href {href!r} must not contain query or fragment data"
    return None


def _decode_include_path(source: Path, href: str) -> tuple[Path | None, str | None]:
    decoded_path = unquote(urlsplit(href).path)
    include_path = Path(decoded_path)

    if include_path.is_absolute():
        return None, f"{source}: XInclude href {href!r} must be a relative includes/ path"

    parts = include_path.parts
    if not parts or parts[0] != ALLOWED_INCLUDE_DIR or ".." in parts:
        return None, f"{source}: XInclude href {href!r} must stay under includes/"
    return include_path, None


def _validate_include_target(source: Path, href: str, include_path: Path) -> str | None:
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


def _validate_href(source: Path, href: str) -> str | None:
    url_error = _validate_url_boundary(source, href)
    if url_error:
        return url_error

    include_path, path_error = _decode_include_path(source, href)
    if path_error:
        return path_error
    if include_path is None:
        return f"{source}: XInclude href {href!r} must stay under includes/"

    return _validate_include_target(source, href, include_path)


def validate_xinclude_paths(path: str | Path) -> list[str]:
    """Return XInclude boundary errors for one XML file."""

    source = Path(path)
    try:
        root = ET.parse(source).getroot()
    except OSError as exc:
        return [f"{source}: cannot read XML file: {exc}"]
    except DefusedXmlException as exc:
        return [f"{source}: unsafe XML rejected before XInclude expansion: {exc}"]
    except ET.ParseError as exc:
        return [f"{source}: cannot parse XML before XInclude expansion: {exc}"]

    errors: list[str] = []
    for include in _include_elements(root):
        href = include.attrib.get("href")
        if not href:
            errors.append(f"{source}: XInclude element missing href")
            continue
        error = _validate_href(source, href)
        if error:
            errors.append(error)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate repository XInclude hrefs before xmllint expansion."
    )
    parser.add_argument("paths", nargs="+", help="XML files to check")
    args = parser.parse_args(argv)

    errors: list[str] = []
    for path in args.paths:
        errors.extend(validate_xinclude_paths(path))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
