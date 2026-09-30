from __future__ import annotations

import re

import pytest

from curious_signals.contract import load_contract
from curious_signals.xml_contracts import validate_phyphox
from tests.conftest import error_text


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        (' version="1.7"', "", "version"),
        ('offset="4"', 'offset="7"', "offset"),
        ('conversion="float32LittleEndian"', 'conversion="int16BigEndian"', "conversion"),
    ],
)
def test_validator_rejects_required_shape_and_wire_contract_breaks(
    valid_phyphox_xml: str, phyphox_file, before: str, after: str, expected: str
) -> None:
    errors = validate_phyphox(phyphox_file(valid_phyphox_xml.replace(before, after, 1)))

    assert expected in error_text(errors)


@pytest.mark.parametrize(
    ("xml", "expected"),
    [
        ('<experiment version="1.7"></experiment>', "root"),
        ("missing-containers", "data-containers"),
    ],
)
def test_validator_rejects_wrong_root_and_missing_required_containers(
    valid_phyphox_xml: str, phyphox_file, xml: str, expected: str
) -> None:
    candidate = (
        xml
        if xml.startswith("<experiment")
        else re.sub(
            r"<data-containers>.*?</data-containers>", "", valid_phyphox_xml, flags=re.DOTALL
        )
    )

    assert expected in error_text(validate_phyphox(phyphox_file(candidate)))


def test_validator_rejects_unsafe_xml_without_disclosing_entity_contents(phyphox_file) -> None:
    errors = validate_phyphox(
        phyphox_file(
            '<!DOCTYPE phyphox [<!ENTITY secret "must-not-leak">]>'
            '<phyphox version="1.7">&secret;</phyphox>'
        )
    )

    diagnostic = error_text(errors)
    assert "unsafe" in diagnostic
    assert "must-not-leak" not in diagnostic


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        ("<container>CH2</container>", "<container>CH1</container>", "duplicate"),
        ('<input axis="x">CH1</input>', '<input axis="x">MISSING</input>', "missing"),
        ('offset="16"', 'offset="0"', "duplicate"),
        ('char="config"', 'char="other"', "config"),
    ],
)
def test_validator_reports_container_bluetooth_offset_and_config_errors(
    valid_phyphox_xml: str, phyphox_file, before: str, after: str, expected: str
) -> None:
    errors = validate_phyphox(phyphox_file(valid_phyphox_xml.replace(before, after, 1)))

    assert expected in error_text(errors)


def _with_contract_uuids(xml: str) -> str:
    bluetooth = load_contract()["bluetooth"]
    return xml.replace('char="data"', f'char="{bluetooth["data_char_uuid"]}"').replace(
        'char="config"', f'char="{bluetooth["config_char_uuid"]}"'
    )


def test_validator_rejects_swapped_offset_to_channel_mapping(
    valid_phyphox_xml: str, phyphox_file
) -> None:
    valid = _with_contract_uuids(valid_phyphox_xml)
    swapped = valid.replace('offset="0"', 'offset="swap"', 1)
    swapped = swapped.replace('offset="4"', 'offset="0"', 1).replace(
        'offset="swap"', 'offset="4"', 1
    )

    errors = validate_phyphox(phyphox_file(swapped))

    assert "offset-to-channel mapping" in error_text(errors)


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        ('offset="4">CH2</output>', 'offset="4">CH1</output>', "duplicate"),
        (
            '<output char="data" conversion="float32LittleEndian" offset="16">CH5</output>',
            "",
            "mapping",
        ),
        ('extra="time">CH0</output>', 'extra="time">CH1</output>', "ch0"),
        ('char="data" conversion=', 'char="wrong" conversion=', "uuid"),
    ],
)
def test_validator_rejects_incomplete_or_inexact_bluetooth_mappings(
    valid_phyphox_xml: str,
    phyphox_file,
    before: str,
    after: str,
    expected: str,
) -> None:
    candidate = _with_contract_uuids(valid_phyphox_xml.replace(before, after, 1))

    assert expected in error_text(validate_phyphox(phyphox_file(candidate)))


@pytest.mark.parametrize("value", ["NaN", "Infinity", "1.5", "7"])
def test_validator_rejects_non_finite_or_inactive_config_modes(
    valid_phyphox_xml: str, phyphox_file, value: str
) -> None:
    candidate = _with_contract_uuids(valid_phyphox_xml.replace(">1</config>", f">{value}</config>"))

    assert "config" in error_text(validate_phyphox(phyphox_file(candidate)))


def test_validator_matches_config_mode_to_known_filename(valid_phyphox_xml: str, tmp_path) -> None:
    candidate = tmp_path / "accelerometer_plot_v1-2.phyphox"
    candidate.write_text(
        _with_contract_uuids(valid_phyphox_xml.replace(">1</config>", ">2</config>")),
        encoding="utf-8",
    )

    assert "filename mode 1" in error_text(validate_phyphox(candidate))
