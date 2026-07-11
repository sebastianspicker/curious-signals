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


def _write_source(tmp_path: Path, xml: str) -> Path:
    source = tmp_path / "experiment.phyphox.xml"
    source.write_text(xml, encoding="utf-8")
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

    if returncode != 1:
        pytest.fail(f"expected unsafe include failure, got {returncode}")
    if "must stay under includes/" not in stderr.getvalue():
        pytest.fail("expected unsafe include diagnostic")


def test_rejects_internal_entity_declaration(tmp_path: Path) -> None:
    source = _write_source(
        tmp_path,
        '<!DOCTYPE phyphox [<!ENTITY injected "unsafe">]><phyphox>&injected;</phyphox>',
    )

    errors = validate_xinclude_paths(source)

    assert len(errors) == 1
    assert "unsafe XML rejected before XInclude expansion" in errors[0]


def test_rejects_external_entity_declaration(tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("must-not-be-read", encoding="utf-8")
    source = _write_source(
        tmp_path,
        f'<!DOCTYPE phyphox [<!ENTITY external SYSTEM "{secret.as_uri()}">]>'
        "<phyphox>&external;</phyphox>",
    )

    errors = validate_xinclude_paths(source)

    assert len(errors) == 1
    assert "unsafe XML rejected before XInclude expansion" in errors[0]
    assert "must-not-be-read" not in errors[0]


def test_rejects_entity_expansion_payload(tmp_path: Path) -> None:
    source = _write_source(
        tmp_path,
        textwrap.dedent("""\
            <!DOCTYPE phyphox [
                <!ENTITY a "1234567890">
                <!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">
                <!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;&b;&b;">
            ]>
            <phyphox>&c;</phyphox>
        """),
    )

    errors = validate_xinclude_paths(source)

    assert len(errors) == 1
    assert "unsafe XML rejected before XInclude expansion" in errors[0]


def test_malformed_xml_keeps_controlled_parse_diagnostic(tmp_path: Path) -> None:
    source = _write_source(tmp_path, "<phyphox>")

    errors = validate_xinclude_paths(source)

    assert len(errors) == 1
    assert "cannot parse XML before XInclude expansion" in errors[0]


def test_cli_rejects_unsafe_xml_without_traceback(tmp_path: Path) -> None:
    source = _write_source(
        tmp_path,
        '<!DOCTYPE phyphox [<!ENTITY injected "unsafe">]><phyphox>&injected;</phyphox>',
    )
    stderr = io.StringIO()

    with redirect_stderr(stderr):
        returncode = main([str(source)])

    assert returncode == 1
    assert "unsafe XML rejected before XInclude expansion" in stderr.getvalue()
    assert "Traceback" not in stderr.getvalue()
