"""Tests for tools/validate_phyphox.py"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from validate_phyphox import (
    ValidationError,
    _child,
    _children,
    _local_name,
    _text,
    main,
    validate_phyphox,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_VALID_XML = textwrap.dedent("""\
    <phyphox version="1.7" locale="en">
        <title>Test</title>
        <category>Cat</category>
        <description>Desc</description>
        <data-containers>
            <container size="0" static="false" init="">CH0</container>
            <container size="0" static="false" init="">CH1</container>
            <container size="0" static="false" init="">CH2</container>
            <container size="0" static="false" init="">CH3</container>
            <container size="0" static="false" init="">CH4</container>
            <container size="0" static="false" init="">CH5</container>
        </data-containers>
        <input>
            <bluetooth mode="notification" rate="1" subscribeOnStart="false" id="Sense">
                <output extra="time">CH0</output>
                <output char="cddf1002-30f7-4671-8b43-5e40ba53514a" offset="0">CH1</output>
                <output char="cddf1002-30f7-4671-8b43-5e40ba53514a" offset="4">CH2</output>
                <output char="cddf1002-30f7-4671-8b43-5e40ba53514a" offset="8">CH3</output>
                <output char="cddf1002-30f7-4671-8b43-5e40ba53514a" offset="12">CH4</output>
                <output char="cddf1002-30f7-4671-8b43-5e40ba53514a" offset="16">CH5</output>
            </bluetooth>
        </input>
        <output>
            <bluetooth id="Sense">
                <config
                    char="cddf1003-30f7-4671-8b43-5e40ba53514a"
                    conversion="float32LittleEndian"
                >1.0</config>
            </bluetooth>
        </output>
        <views>
            <view label="Graph">
                <graph label="Test">
                    <input axis="x">CH1</input>
                    <input axis="y">CH2</input>
                </graph>
            </view>
        </views>
    </phyphox>
""")


@pytest.fixture()
def valid_phyphox_file(tmp_path):
    """Write a minimal valid phyphox XML and return its path."""
    p = tmp_path / "valid.phyphox"
    p.write_text(MINIMAL_VALID_XML, encoding="utf-8")
    return str(p)


@pytest.fixture()
def xml_factory(tmp_path):
    """Factory fixture: write arbitrary XML content to a temp file and return path."""
    counter = 0

    def _make(content: str, suffix: str = ".phyphox") -> str:
        nonlocal counter
        counter += 1
        p = tmp_path / f"test_{counter}{suffix}"
        p.write_text(content, encoding="utf-8")
        return str(p)

    return _make


# ---------------------------------------------------------------------------
# Helper function unit tests
# ---------------------------------------------------------------------------


class TestLocalName:
    def test_plain_tag(self):
        assert _local_name("phyphox") == "phyphox"

    def test_namespaced_tag(self):
        assert _local_name("{http://example.com}phyphox") == "phyphox"

    def test_empty_namespace(self):
        assert _local_name("{}phyphox") == "phyphox"

    def test_no_closing_brace(self):
        # No '}' means it is returned as-is
        assert _local_name("{broken") == "{broken"


class TestChild:
    def test_finds_child(self):
        import xml.etree.ElementTree as ET

        root = ET.fromstring("<root><child/></root>")
        assert _child(root, "child") is not None

    def test_returns_none_when_missing(self):
        import xml.etree.ElementTree as ET

        root = ET.fromstring("<root><child/></root>")
        assert _child(root, "missing") is None

    def test_finds_first_of_multiple(self):
        import xml.etree.ElementTree as ET

        root = ET.fromstring("<root><child>A</child><child>B</child></root>")
        found = _child(root, "child")
        assert found is not None
        assert found.text == "A"


class TestChildren:
    def test_returns_all_matching(self):
        import xml.etree.ElementTree as ET

        root = ET.fromstring("<root><a/><b/><a/></root>")
        result = _children(root, "a")
        assert len(result) == 2

    def test_returns_empty_when_none(self):
        import xml.etree.ElementTree as ET

        root = ET.fromstring("<root><a/></root>")
        assert _children(root, "b") == []


class TestText:
    def test_returns_text(self):
        import xml.etree.ElementTree as ET

        elem = ET.fromstring("<e>hello</e>")
        assert _text(elem) == "hello"

    def test_strips_whitespace(self):
        import xml.etree.ElementTree as ET

        elem = ET.fromstring("<e>  hello  </e>")
        assert _text(elem) == "hello"

    def test_returns_none_for_none(self):
        assert _text(None) is None

    def test_returns_none_for_empty(self):
        import xml.etree.ElementTree as ET

        elem = ET.fromstring("<e></e>")
        assert _text(elem) is None

    def test_returns_none_for_whitespace_only(self):
        import xml.etree.ElementTree as ET

        elem = ET.fromstring("<e>   </e>")
        assert _text(elem) is None


# ---------------------------------------------------------------------------
# File-level error handling
# ---------------------------------------------------------------------------


class TestFileErrors:
    def test_missing_file(self, tmp_path):
        path = str(tmp_path / "nonexistent.phyphox")
        errors = validate_phyphox(path)
        assert len(errors) == 1
        assert "cannot read file" in errors[0].message

    def test_malformed_xml(self, xml_factory):
        path = xml_factory("<not-closed")
        errors = validate_phyphox(path)
        assert len(errors) == 1
        assert "XML parse error" in errors[0].message

    def test_empty_file(self, xml_factory):
        path = xml_factory("")
        errors = validate_phyphox(path)
        assert len(errors) == 1
        assert "XML parse error" in errors[0].message

    def test_valid_xml_wrong_root(self, xml_factory):
        path = xml_factory("<experiment></experiment>")
        errors = validate_phyphox(path)
        assert any("root element must be <phyphox>" in e.message for e in errors)


# ---------------------------------------------------------------------------
# Valid file produces no errors
# ---------------------------------------------------------------------------


class TestValidFile:
    def test_minimal_valid_passes(self, valid_phyphox_file):
        errors = validate_phyphox(valid_phyphox_file)
        assert errors == []


# ---------------------------------------------------------------------------
# <phyphox> attributes
# ---------------------------------------------------------------------------


class TestPhyphoxAttributes:
    def test_missing_version(self, xml_factory):
        xml = MINIMAL_VALID_XML.replace(' version="1.7"', "")
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("missing required attribute version" in e.message for e in errors)


# ---------------------------------------------------------------------------
# Required top-level elements
# ---------------------------------------------------------------------------


class TestRequiredTopLevel:
    @pytest.mark.parametrize(
        "element",
        [
            "title",
            "category",
            "description",
            "data-containers",
            "input",
            "views",
        ],
    )
    def test_missing_required_element(self, xml_factory, element):
        # Remove the element by stripping its opening and closing tags.
        # This is a rough approach but works for our minimal XML.
        import re

        xml = re.sub(
            rf"<{element}[\s>].*?</{element}>",
            "",
            MINIMAL_VALID_XML,
            flags=re.DOTALL,
        )
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any(f"missing required top-level <{element}>" in e.message for e in errors)


# ---------------------------------------------------------------------------
# Data container validation
# ---------------------------------------------------------------------------


class TestDataContainers:
    def test_empty_container_name(self, xml_factory):
        xml = MINIMAL_VALID_XML.replace(
            '<container size="0" static="false" init="">CH0</container>',
            '<container size="0" static="false" init="">  </container>',
        )
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("must have non-empty text" in e.message for e in errors)

    def test_duplicate_container_names(self, xml_factory):
        xml = MINIMAL_VALID_XML.replace(
            '<container size="0" static="false" init="">CH2</container>',
            '<container size="0" static="false" init="">CH1</container>',
        )
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("duplicate <container> names" in e.message for e in errors)

    def test_unknown_container_reference(self, xml_factory):
        # Reference a container that does not exist in <data-containers>
        xml = MINIMAL_VALID_XML.replace(
            '<input axis="x">CH1</input>',
            '<input axis="x">NONEXISTENT</input>',
        )
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("references unknown data containers" in e.message for e in errors)
        assert any("NONEXISTENT" in e.message for e in errors)


# ---------------------------------------------------------------------------
# Bluetooth input/output validation
# ---------------------------------------------------------------------------


class TestBluetoothValidation:
    def test_missing_bluetooth_id(self, xml_factory):
        xml = MINIMAL_VALID_XML.replace(' id="Sense"', "", 1)
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("missing required attribute id" in e.message for e in errors)

    def test_missing_extra_time(self, xml_factory):
        xml = MINIMAL_VALID_XML.replace(
            '<output extra="time">CH0</output>\n',
            "",
        )
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any('missing bluetooth <output extra="time">' in e.message for e in errors)

    def test_bluetooth_id_mismatch(self, xml_factory):
        # Change the output bluetooth id to differ from input
        xml = MINIMAL_VALID_XML.replace(
            '<bluetooth id="Sense">',
            '<bluetooth id="Other">',
            1,  # only replace the first occurrence (in <input>)
        )
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("bluetooth id mismatch" in e.message for e in errors)

    def test_invalid_offset(self, xml_factory):
        xml = MINIMAL_VALID_XML.replace('offset="0"', 'offset="abc"')
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("invalid bluetooth output offset" in e.message for e in errors)

    def test_missing_output_section(self, xml_factory):
        import re

        xml = re.sub(
            r"<output>\s*<bluetooth.*?</output>",
            "",
            MINIMAL_VALID_XML,
            flags=re.DOTALL,
        )
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("missing <output>" in e.message for e in errors)

    def test_multiple_bluetooth_input_blocks(self, xml_factory):
        extra_bt = textwrap.dedent("""\
            <bluetooth mode="notification" rate="1" subscribeOnStart="false" id="Second">
                <output extra="time">CH0</output>
                <output char="cddf1002-30f7-4671-8b43-5e40ba53514a" offset="0">CH1</output>
                <output char="cddf1002-30f7-4671-8b43-5e40ba53514a" offset="4">CH2</output>
            </bluetooth>
        """)
        xml = MINIMAL_VALID_XML.replace(
            "</input>",
            extra_bt + "</input>",
        )
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("expected exactly one <input><bluetooth> block" in e.message for e in errors)


# ---------------------------------------------------------------------------
# Config element validation
# ---------------------------------------------------------------------------


class TestConfigValidation:
    def test_wrong_conversion(self, xml_factory):
        xml = MINIMAL_VALID_XML.replace(
            'conversion="float32LittleEndian"',
            'conversion="int16BigEndian"',
        )
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("expected config conversion float32LittleEndian" in e.message for e in errors)

    def test_missing_config_char(self, xml_factory):
        import re

        xml = re.sub(
            r'\s+char="cddf1003-30f7-4671-8b43-5e40ba53514a"',
            "",
            MINIMAL_VALID_XML,
            count=1,
        )
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("<config> missing required attribute char" in e.message for e in errors)

    def test_non_numeric_config_value(self, xml_factory):
        xml = MINIMAL_VALID_XML.replace(
            ">1.0</config>",
            ">not_a_number</config>",
        )
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("not numeric" in e.message for e in errors)

    def test_empty_config_value(self, xml_factory):
        xml = MINIMAL_VALID_XML.replace(
            ">1.0</config>",
            "> </config>",
        )
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("<config> must have a numeric value" in e.message for e in errors)


# ---------------------------------------------------------------------------
# Analysis / export container references
# ---------------------------------------------------------------------------


class TestContainerReferences:
    def test_analysis_references_checked(self, xml_factory):
        analysis_block = textwrap.dedent("""\
            <analysis sleep="0" onUserInput="false">
                <formula formula="[1_]*9.81">
                    <input clear="false">CH2</input>
                    <output>GHOST</output>
                </formula>
            </analysis>
        """)
        xml = MINIMAL_VALID_XML.replace("</phyphox>", analysis_block + "</phyphox>")
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("GHOST" in e.message for e in errors)

    def test_export_references_checked(self, xml_factory):
        export_block = textwrap.dedent("""\
            <export>
                <set name="Data">
                    <data name="col">PHANTOM</data>
                </set>
            </export>
        """)
        xml = MINIMAL_VALID_XML.replace("</phyphox>", export_block + "</phyphox>")
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("PHANTOM" in e.message for e in errors)


# ---------------------------------------------------------------------------
# ValidationError dataclass
# ---------------------------------------------------------------------------


class TestValidationError:
    def test_is_frozen(self):
        ve = ValidationError("test")
        with pytest.raises(AttributeError):
            ve.message = "changed"

    def test_message_stored(self):
        ve = ValidationError("hello")
        assert ve.message == "hello"


# ---------------------------------------------------------------------------
# Offset validation specifics
# ---------------------------------------------------------------------------


class TestOffsetPlausibility:
    def test_non_standard_offsets_reported(self, xml_factory):
        """Offsets that do not match {0,4,8,12,16} should be flagged."""
        xml = MINIMAL_VALID_XML.replace('offset="4"', 'offset="7"')
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("expected float32 offsets" in e.message for e in errors)

    def test_missing_offset_on_non_time_output_reported(self, xml_factory):
        xml = MINIMAL_VALID_XML.replace(
            "</bluetooth>",
            '<output char="cddf1002-30f7-4671-8b43-5e40ba53514a">CH5</output></bluetooth>',
            1,
        )
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("missing required bluetooth output offset" in e.message for e in errors)


# ---------------------------------------------------------------------------
# Multiple output bluetooth blocks
# ---------------------------------------------------------------------------


class TestOutputBluetoothBlocks:
    def test_multiple_output_bluetooth_blocks(self, xml_factory):
        extra = textwrap.dedent("""\
            <bluetooth id="Sense">
                <config
                    char="cddf1003-30f7-4671-8b43-5e40ba53514a"
                    conversion="float32LittleEndian"
                >2.0</config>
            </bluetooth>
        """)
        xml = MINIMAL_VALID_XML.replace(
            "</output>",
            extra + "</output>",
        )
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("expected exactly one <output><bluetooth> block" in e.message for e in errors)

    def test_multiple_config_blocks(self, xml_factory):
        extra_cfg = (
            '<config char="cddf1003-30f7-4671-8b43-5e40ba53514a" '
            'conversion="float32LittleEndian">2.0</config>'
        )
        xml = MINIMAL_VALID_XML.replace(
            "</bluetooth>\n    </output>",
            extra_cfg + "\n</bluetooth>\n    </output>",
        )
        path = xml_factory(xml)
        errors = validate_phyphox(path)
        assert any("expected exactly one <output><bluetooth><config>" in e.message for e in errors)


# ---------------------------------------------------------------------------
# main() CLI entry point
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = REPO_ROOT / "experiments"


class TestMainCli:
    """Tests for the validate_phyphox.main() CLI entry point."""

    def test_valid_generated_file_returns_zero(self) -> None:
        """main() with a known-good generated experiment should return 0."""
        sample = next(GENERATED_DIR.glob("*.phyphox"), None)
        assert sample is not None, "No generated .phyphox files found in experiments/"
        assert main([str(sample)]) == 0

    def test_invalid_file_returns_one_and_prints_to_stderr(self, xml_factory, capsys) -> None:
        """main() with a file that fails validation should return 1 and print errors."""
        bad_xml = MINIMAL_VALID_XML.replace(
            'char="cddf1002-30f7-4671-8b43-5e40ba53514a"',
            'char="deadbeef-0000-0000-0000-000000000000"',
        )
        path = xml_factory(bad_xml)
        result = main([str(path)])
        captured = capsys.readouterr()
        assert result == 1
        assert captured.err  # at least one error line must appear on stderr

    def test_nonexistent_path_returns_one(self, capsys) -> None:
        """main() with a path that does not exist should return 1."""
        result = main(["/nonexistent/path/that/cannot/exist.phyphox"])
        captured = capsys.readouterr()
        assert result == 1
        assert captured.err

    def test_multiple_valid_files_all_pass(self) -> None:
        """main() accepts multiple file arguments and passes when all are valid."""
        samples = list(GENERATED_DIR.glob("*.phyphox"))
        assert samples, "No generated .phyphox files found in experiments/"
        assert main([str(p) for p in samples]) == 0
