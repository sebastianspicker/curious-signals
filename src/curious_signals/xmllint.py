"""The xmllint boundary: locating the executable, running it, and XInclude expansion."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from . import ToolError
from .xinclude import XINCLUDE_NS

XML_BASE_ATTRIBUTE_RE = re.compile(r'\s+xml:base="[^"]*"')
XINCLUDE_NAMESPACE_DECLARATION = f' xmlns:xi="{XINCLUDE_NS}"'


def find_xmllint() -> str:
    executable = shutil.which("xmllint")
    if executable is None:
        raise ToolError("xmllint not found. Install libxml2 utilities first.")
    return executable


def run_xmllint(arguments: list[str]) -> str:
    """Run xmllint and return its stdout, raising ToolError when it fails."""

    try:
        result = subprocess.run(arguments, check=False, capture_output=True, text=True)
    except OSError as error:
        raise ToolError(f"cannot run xmllint: {error}") from error
    if result.returncode:
        raise ToolError(result.stderr.strip() or result.stdout.strip() or "xmllint failed")
    return result.stdout


def strip_xinclude_metadata(xml_text: str) -> str:
    """Strip generator-only XML base metadata without changing experiment XML."""

    return XML_BASE_ATTRIBUTE_RE.sub("", xml_text).replace(XINCLUDE_NAMESPACE_DECLARATION, "")


def expand_xincludes(source: Path, executable: str) -> str:
    """Expand XIncludes in a source file and strip the generator-only metadata."""

    return strip_xinclude_metadata(run_xmllint([executable, "--xinclude", str(source)]))
