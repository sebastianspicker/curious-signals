from __future__ import annotations

import pytest

from curious_signals.xinclude import validate_xinclude_paths
from tests.conftest import error_text

XINCLUDE = "http://www.w3.org/2001/XInclude"
LIBXML_ALTERNATE_XINCLUDE = "http://www.w3.org/2003/XInclude"


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


def test_xinclude_rejects_libxml_alternate_namespace(tmp_path) -> None:
    source = tmp_path / "alternate.phyphox.xml"
    source.write_text(
        f'<phyphox xmlns:xi="{LIBXML_ALTERNATE_XINCLUDE}">'
        '<xi:include href="outside.xml"/></phyphox>',
        encoding="utf-8",
    )

    assert "namespace" in error_text(validate_xinclude_paths(source))


def test_xinclude_recursively_validates_nested_documents(tmp_path) -> None:
    source = write_include_source(tmp_path, "includes/allowed.xml")
    nested = source.parent / "includes" / "nested.xml"
    nested.write_text("<nodes><node>nested</node></nodes>", encoding="utf-8")
    (source.parent / "includes" / "allowed.xml").write_text(
        f'<nodes xmlns:xi="{XINCLUDE}"><xi:include href="nested.xml"/></nodes>',
        encoding="utf-8",
    )

    assert validate_xinclude_paths(source) == []


def test_standalone_include_fragment_accepts_nested_sibling(tmp_path) -> None:
    includes = tmp_path / "includes"
    includes.mkdir()
    nested = includes / "nested.xml"
    nested.write_text("<nodes/>", encoding="utf-8")
    fragment = includes / "fragment.xml"
    fragment.write_text(
        f'<nodes xmlns:xi="{XINCLUDE}"><xi:include href="nested.xml"/></nodes>',
        encoding="utf-8",
    )

    assert validate_xinclude_paths(fragment) == []

    subdirectory = includes / "sub"
    subdirectory.mkdir()
    (subdirectory / "child.xml").write_text("<nodes/>", encoding="utf-8")
    nested_fragment = subdirectory / "fragment.xml"
    nested_fragment.write_text(
        f'<nodes xmlns:xi="{XINCLUDE}"><xi:include href="child.xml"/></nodes>',
        encoding="utf-8",
    )

    assert validate_xinclude_paths(nested_fragment, allowed_root=includes) == []


@pytest.mark.parametrize(
    ("nested_content", "expected"),
    [
        (
            f'<nodes xmlns:xi="{XINCLUDE}"><xi:include href="../outside.xml"/></nodes>',
            "includes",
        ),
        ("<!DOCTYPE nodes><nodes/>", "unsafe"),
        ('<nodes xml:base="https://example.invalid/"/>', "xml:base"),
        (
            f'<nodes xmlns:xi="{LIBXML_ALTERNATE_XINCLUDE}">'
            '<xi:include href="../outside.xml"/></nodes>',
            "namespace",
        ),
    ],
)
def test_xinclude_rejects_nested_boundary_and_parser_bypasses(
    tmp_path, nested_content: str, expected: str
) -> None:
    source = write_include_source(tmp_path, "includes/allowed.xml")
    (source.parent / "includes" / "allowed.xml").write_text(nested_content, encoding="utf-8")

    assert expected in error_text(validate_xinclude_paths(source))


def test_xinclude_rejects_xml_base_and_text_inclusion(tmp_path) -> None:
    base_source = write_include_source(tmp_path / "base", "includes/allowed.xml")
    base_source.write_text(
        f'<phyphox xmlns:xi="{XINCLUDE}" xml:base="includes/">'
        '<xi:include href="allowed.xml"/></phyphox>',
        encoding="utf-8",
    )
    text_source = write_include_source(tmp_path / "text", "includes/allowed.xml")
    text_source.write_text(
        f'<phyphox xmlns:xi="{XINCLUDE}">'
        '<xi:include href="includes/allowed.xml" parse="text"/></phyphox>',
        encoding="utf-8",
    )

    assert "xml:base" in error_text(validate_xinclude_paths(base_source))
    assert "xml parsing" in error_text(validate_xinclude_paths(text_source))


def test_xinclude_rejects_symlinked_document_and_include_root(tmp_path) -> None:
    real_source = write_include_source(tmp_path / "document", "includes/allowed.xml")
    symlink_source = tmp_path / "document-link.xml"
    symlink_source.symlink_to(real_source)

    source_dir = tmp_path / "root"
    source_dir.mkdir()
    external_includes = tmp_path / "external-includes"
    external_includes.mkdir()
    (external_includes / "allowed.xml").write_text("<nodes/>", encoding="utf-8")
    (source_dir / "includes").symlink_to(external_includes, target_is_directory=True)
    root_source = source_dir / "experiment.phyphox.xml"
    root_source.write_text(
        f'<phyphox xmlns:xi="{XINCLUDE}"><xi:include href="includes/allowed.xml"/></phyphox>',
        encoding="utf-8",
    )

    assert "symlink" in error_text(validate_xinclude_paths(symlink_source))
    assert "symlink" in error_text(validate_xinclude_paths(root_source))


def test_xinclude_rejects_symlinked_configured_source_root(tmp_path) -> None:
    real_root = tmp_path / "real-source"
    real_source = write_include_source(real_root, "includes/allowed.xml")
    linked_root = tmp_path / "linked-source"
    linked_root.symlink_to(real_root, target_is_directory=True)

    errors = validate_xinclude_paths(
        linked_root / real_source.name, allowed_root=linked_root / "includes"
    )

    assert "source root" in error_text(errors)
    assert "symlink" in error_text(errors)


def test_xinclude_rejects_symlinks_inside_include_graph(tmp_path) -> None:
    source = write_include_source(tmp_path, "includes/link.xml")
    subdirectory = source.parent / "includes" / "sub"
    subdirectory.mkdir()
    (subdirectory / "document.xml").write_text("<nodes/>", encoding="utf-8")
    (source.parent / "includes" / "link.xml").symlink_to(subdirectory / "document.xml")

    assert "symlink" in error_text(validate_xinclude_paths(source))


@pytest.mark.parametrize("href", ["http://[::1", "includes/%00.xml"])
def test_xinclude_reports_malformed_hrefs_without_crashing(tmp_path, href: str) -> None:
    errors = validate_xinclude_paths(write_include_source(tmp_path, href))

    assert errors
