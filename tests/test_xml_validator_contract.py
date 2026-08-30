from __future__ import annotations

import re

import pytest

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
