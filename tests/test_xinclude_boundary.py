from __future__ import annotations

import pytest

from curious_signals.xinclude import validate_xinclude_paths
from tests.conftest import error_text

XINCLUDE = "http://www.w3.org/2001/XInclude"


def write_include_source(tmp_path, href: str) -> object:
    includes = tmp_path / "includes"
    includes.mkdir(parents=True)
    (includes / "allowed.xml").write_text("<nodes><node>ok</node></nodes>", encoding="utf-8")
    source = tmp_path / "experiment.phyphox.xml"
    source.write_text(
        f'<phyphox xmlns:xi="{XINCLUDE}"><xi:include href="{href}"/></phyphox>',
        encoding="utf-8",
    )
    return source


@pytest.mark.parametrize(
    ("href", "expected"),
    [
        ("https://example.invalid/include.xml", "url"),
        ("/etc/hosts", "relative"),
        ("../outside.xml", "includes"),
        ("includes/missing.xml", "exist"),
        ("includes/allowed.xml#node", "fragment"),
    ],
)
def test_xinclude_rejects_non_local_or_missing_targets(tmp_path, href: str, expected: str) -> None:
    errors = validate_xinclude_paths(write_include_source(tmp_path, href))

    assert expected in error_text(errors)


def test_xinclude_rejects_directory_and_symlink_escape(tmp_path) -> None:
    directory_source = write_include_source(tmp_path / "directory", "includes/folder")
    (directory_source.parent / "includes" / "folder").mkdir()
    outside = tmp_path / "outside.xml"
    outside.write_text("<nodes/>", encoding="utf-8")
    symlink_source = write_include_source(tmp_path / "symlink", "includes/escape.xml")
    (symlink_source.parent / "includes" / "escape.xml").symlink_to(outside)

    assert "file" in error_text(validate_xinclude_paths(directory_source))
    assert "includes" in error_text(validate_xinclude_paths(symlink_source))


def test_xinclude_rejects_entity_payload_before_resolution(tmp_path) -> None:
    source = tmp_path / "unsafe.phyphox.xml"
    source.write_text(
        '<!DOCTYPE phyphox [<!ENTITY injected "unsafe">]><phyphox>&injected;</phyphox>',
        encoding="utf-8",
    )

    assert "unsafe" in error_text(validate_xinclude_paths(source))
