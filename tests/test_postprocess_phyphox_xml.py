"""Tests for tools/postprocess_phyphox_xml.py"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

from postprocess_phyphox_xml import postprocess

_SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "postprocess_phyphox_xml.py"

# ---------------------------------------------------------------------------
# postprocess() unit tests
# ---------------------------------------------------------------------------


class TestPostprocessXmlBase:
    """Tests for xml:base attribute removal."""

    def test_removes_single_xml_base(self):
        xml = '<container xml:base="includes/foo.xml">CH0</container>'
        result = postprocess(xml)
        assert "xml:base" not in result
        assert "<container>CH0</container>" == result

    def test_removes_multiple_xml_base(self):
        xml = textwrap.dedent("""\
            <root>
                <a xml:base="path/a.xml">A</a>
                <b xml:base="path/b.xml">B</b>
            </root>
        """)
        result = postprocess(xml)
        assert "xml:base" not in result
        assert "<a>A</a>" in result
        assert "<b>B</b>" in result

    def test_preserves_other_attributes(self):
        xml = '<container size="0" xml:base="x.xml" static="false">CH0</container>'
        result = postprocess(xml)
        assert "xml:base" not in result
        assert 'size="0"' in result
        assert 'static="false"' in result

    def test_no_xml_base_unchanged(self):
        xml = '<container size="0">CH0</container>'
        assert postprocess(xml) == xml


class TestPostprocessXIncludeNamespace:
    """Tests for XInclude namespace removal."""

    def test_removes_xi_namespace(self):
        xml = '<phyphox xmlns:xi="http://www.w3.org/2001/XInclude"><title>T</title></phyphox>'
        result = postprocess(xml)
        assert "xmlns:xi" not in result
        assert "<phyphox><title>T</title></phyphox>" == result

    def test_no_xi_namespace_unchanged(self):
        xml = "<phyphox><title>T</title></phyphox>"
        assert postprocess(xml) == xml


class TestPostprocessCombined:
    """Tests combining both transformations."""

    def test_both_removals(self):
        xml = textwrap.dedent("""\
            <phyphox xmlns:xi="http://www.w3.org/2001/XInclude" version="1.7">
                <data-containers>
                    <container xml:base="includes/containers.xml" size="0">CH0</container>
                </data-containers>
            </phyphox>
        """)
        result = postprocess(xml)
        assert "xmlns:xi" not in result
        assert "xml:base" not in result
        assert 'version="1.7"' in result
        assert "<container" in result


class TestPostprocessEdgeCases:
    """Edge cases for postprocess()."""

    def test_empty_string(self):
        assert postprocess("") == ""

    def test_whitespace_only(self):
        assert postprocess("   \n\n  ") == "   \n\n  "

    def test_xml_base_with_special_chars_in_path(self):
        xml = '<e xml:base="path/with spaces/file.xml">X</e>'
        result = postprocess(xml)
        assert "xml:base" not in result
        assert "<e>X</e>" == result

    def test_xml_base_with_nested_quotes_unmatched(self):
        # The regex matches up to the closing double-quote; ensure no breakage
        xml = '<e xml:base="some/path.xml" other="v">X</e>'
        result = postprocess(xml)
        assert "xml:base" not in result
        assert 'other="v"' in result

    def test_preserves_newlines_and_indentation(self):
        xml = textwrap.dedent("""\
            <root>
                <child>text</child>
            </root>
        """)
        assert postprocess(xml) == xml

    def test_multiple_xi_namespace_declarations(self):
        # Only the exact xmlns:xi declaration should be removed
        xml = '<a xmlns:xi="http://www.w3.org/2001/XInclude"> <b xmlns:xi="http://www.w3.org/2001/XInclude"/></a>'
        result = postprocess(xml)
        assert "xmlns:xi" not in result


# ---------------------------------------------------------------------------
# main() integration via subprocess
# ---------------------------------------------------------------------------


class TestMainFileArg:
    """Test the CLI entry point with a file argument."""

    def test_reads_file_and_postprocesses(self, tmp_path):
        import subprocess

        xml = '<phyphox xmlns:xi="http://www.w3.org/2001/XInclude"><title>T</title></phyphox>'
        p = tmp_path / "input.xml"
        p.write_text(xml, encoding="utf-8")

        script = _SCRIPT
        result = subprocess.run(
            [sys.executable, script, str(p)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "xmlns:xi" not in result.stdout
        assert "<phyphox>" in result.stdout

    def test_missing_file_returns_error(self, tmp_path):
        import subprocess

        script = _SCRIPT
        result = subprocess.run(
            [sys.executable, script, str(tmp_path / "missing.xml")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Error" in result.stderr

    def test_stdin_mode(self, tmp_path):
        import subprocess

        xml = '<e xml:base="x.xml">V</e>'
        script = _SCRIPT
        result = subprocess.run(
            [sys.executable, script],
            input=xml,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "xml:base" not in result.stdout
        assert "<e>V</e>" == result.stdout
