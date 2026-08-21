from __future__ import annotations

from pathlib import Path

from postprocess_phyphox_xml import postprocess
from validate_phyphox import validate_phyphox
from validate_xinclude_paths import validate_xinclude_paths


def test_validator_rejects_unsafe_xml_without_repository_fixture(tmp_path: Path) -> None:
    path = tmp_path / "unsafe.phyphox"
    path.write_text(
        '<!DOCTYPE phyphox [<!ENTITY injected "unsafe">]><phyphox>&injected;</phyphox>',
        encoding="utf-8",
    )

    errors = validate_phyphox(path)

    assert any("unsafe XML rejected" in error.message for error in errors)


def test_xinclude_guard_rejects_path_escape(tmp_path: Path) -> None:
    source = tmp_path / "experiment.phyphox.xml"
    source.write_text(
        '<phyphox xmlns:xi="http://www.w3.org/2001/XInclude">'
        '<xi:include href="../outside.xml" xpointer="xpointer(/nodes/node())" />'
        "</phyphox>",
        encoding="utf-8",
    )

    assert any("must stay under includes/" in error for error in validate_xinclude_paths(source))


def test_postprocess_removes_generator_only_xml_attributes() -> None:
    result = postprocess(
        '<phyphox xmlns:xi="http://www.w3.org/2001/XInclude" '
        'xml:base="source.xml"><title>T</title></phyphox>'
    )

    assert "xmlns:xi" not in result
    assert "xml:base" not in result
    assert "<phyphox><title>T</title></phyphox>" == result
