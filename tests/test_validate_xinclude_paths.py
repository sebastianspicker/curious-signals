"""Regression tests for XInclude path boundary checks."""

from __future__ import annotations

import io
import textwrap
from contextlib import redirect_stderr
from pathlib import Path

import pytest
from validate_xinclude_paths import main, validate_xinclude_paths

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPO_ROOT / "src" / "phyphox"
XINCLUDE_NS = "http://www.w3.org/2001/XInclude"


def _source_with_include(tmp_path: Path, href: str) -> Path:
    includes = tmp_path / "includes"
    includes.mkdir()
    (includes / "allowed.xml").write_text("<nodes><node>ok</node></nodes>", encoding="utf-8")

    source = tmp_path / "experiment.phyphox.xml"
    source.write_text(
        textwrap.dedent(
            f"""\
            <phyphox xmlns:xi="{XINCLUDE_NS}">
                <xi:include href="{href}" xpointer="xpointer(/nodes/node())" />
            </phyphox>
            """
        ),
        encoding="utf-8",
    )
    return source


def test_current_source_includes_are_within_allowed_directory() -> None:
    errors: list[str] = []

    for path in sorted(SOURCE_DIR.glob("*.phyphox.xml")):
        errors.extend(validate_xinclude_paths(path))

    assert errors == []


def test_rejects_parent_directory_escape(tmp_path: Path) -> None:
    source = _source_with_include(tmp_path, "../outside.xml")

    errors = validate_xinclude_paths(source)

    assert len(errors) == 1
    assert "must stay under includes/" in errors[0]


def test_rejects_absolute_include_path(tmp_path: Path) -> None:
    source = _source_with_include(tmp_path, "/etc/hosts")

    errors = validate_xinclude_paths(source)

    assert len(errors) == 1
    assert "must be a relative includes/ path" in errors[0]


def test_rejects_url_style_include_path(tmp_path: Path) -> None:
    source = _source_with_include(tmp_path, "https://example.invalid/payload.xml")

    errors = validate_xinclude_paths(source)

    assert len(errors) == 1
    assert "must not use a URL" in errors[0]


@pytest.mark.parametrize(
    ("href", "message"),
    [
        ("includes/allowed.xml?raw=1", "must not contain query or fragment data"),
        ("includes/allowed.xml#payload", "must not contain query or fragment data"),
        ("includes/missing.xml", "XInclude target does not exist"),
    ],
)
def test_rejects_non_plain_file_href(tmp_path: Path, href: str, message: str) -> None:
    source = _source_with_include(tmp_path, href)

    errors = validate_xinclude_paths(source)

    assert len(errors) == 1
    assert message in errors[0]


def test_rejects_directory_include_target(tmp_path: Path) -> None:
    source = _source_with_include(tmp_path, "includes/directory")
    (tmp_path / "includes" / "directory").mkdir()

    errors = validate_xinclude_paths(source)

    assert len(errors) == 1
    assert "XInclude target is not a file" in errors[0]


def test_rejects_symlink_escape_from_includes(tmp_path: Path) -> None:
    source = _source_with_include(tmp_path, "includes/escape.xml")
    outside = tmp_path / "outside.xml"
    outside.write_text("<nodes><node>outside</node></nodes>", encoding="utf-8")
    (tmp_path / "includes" / "escape.xml").symlink_to(outside)

    errors = validate_xinclude_paths(source)

    assert len(errors) == 1
    assert "must stay under includes/" in errors[0]


def test_cli_fails_on_unsafe_include_before_expansion(tmp_path: Path) -> None:
    source = _source_with_include(tmp_path, "../outside.xml")
    stderr = io.StringIO()

    with redirect_stderr(stderr):
        returncode = main([str(source)])

    assert returncode == 1
    assert "must stay under includes/" in stderr.getvalue()
