"""Tests for tools/validate_phyphox.py"""

from __future__ import annotations

import textwrap

import pytest
from validate_phyphox import (
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

    def test_duplicate_offsets_reported(self, xml_factory):
        xml = MINIMAL_VALID_XML.replace('offset="16">CH5', 'offset="0">CH5')
        errors = validate_phyphox(xml_factory(xml))
        assert any("duplicate bluetooth output offsets" in error.message for error in errors)


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
