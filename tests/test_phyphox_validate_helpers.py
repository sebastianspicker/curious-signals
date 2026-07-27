"""Unit tests for validate_phyphox helper functions and mode loading."""

from __future__ import annotations

import json
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import validate_phyphox as validate_module
from validate_phyphox import (
    ValidationError,
    _child,
    _children,
    _load_expected_modes,
    _local_name,
    _text,
)


def _write_mode_repo(tmp_path: Path, mode_values: dict[str, str]) -> Path:
    repo_root = tmp_path / "repo"
    constants_dir = repo_root / "experiments"
    sketch_dir = repo_root / "arduino" / "phyphox_ble_sense"
    source_dir = repo_root / "src" / "phyphox"
    constants_dir.mkdir(parents=True)
    sketch_dir.mkdir(parents=True)
    source_dir.mkdir(parents=True)
    modes = {
        "acceleration": 1,
        "gyroscope": 2,
        "magnetometer": 3,
        "pressure": 4,
        "temperature_humidity": 5,
        "light_rgb": 6,
        "analog_inputs": 9,
    }
    (constants_dir / "phyphox_constants.json").write_text(
        json.dumps({"modes": modes}), encoding="utf-8"
    )
    (sketch_dir / "phyphox_ble_sense.ino").write_text(
        textwrap.dedent("""\
            enum class Mode : int {
              kAcceleration = 1,
              kGyroscope = 2,
              kMagnetometer = 3,
              kPressure = 4,
              kTemperatureHumidity = 5,
              kLightRgb = 6,
              kAnalogInputs = 9,
            };
        """),
        encoding="utf-8",
    )
    for name, value in mode_values.items():
        (source_dir / f"{name}.phyphox.xml").write_text(
            f"<phyphox><output><bluetooth><config>{value}</config></bluetooth></output></phyphox>",
            encoding="utf-8",
        )
    return repo_root


class TestLocalName:
    def test_plain_tag(self):
        assert _local_name("phyphox") == "phyphox"

    def test_namespaced_tag(self):
        assert _local_name("{http://example.com}phyphox") == "phyphox"

    def test_empty_namespace(self):
        assert _local_name("{}phyphox") == "phyphox"

    def test_no_closing_brace(self):
        assert _local_name("{broken") == "{broken"


class TestChild:
    def test_finds_child(self):
        root = ET.fromstring("<root><child/></root>")
        assert _child(root, "child") is not None

    def test_returns_none_when_missing(self):
        root = ET.fromstring("<root><child/></root>")
        assert _child(root, "missing") is None

    def test_finds_first_of_multiple(self):
        root = ET.fromstring("<root><child>A</child><child>B</child></root>")
        found = _child(root, "child")
        assert found is not None
        assert found.text == "A"


class TestChildren:
    def test_returns_all_matching(self):
        root = ET.fromstring("<root><a/><b/><a/></root>")
        assert len(_children(root, "a")) == 2

    def test_returns_empty_when_none(self):
        root = ET.fromstring("<root><a/></root>")
        assert _children(root, "b") == []


class TestText:
    def test_returns_text(self):
        assert _text(ET.fromstring("<e>hello</e>")) == "hello"

    def test_strips_whitespace(self):
        assert _text(ET.fromstring("<e>  hello  </e>")) == "hello"

    def test_returns_none_for_none(self):
        assert _text(None) is None

    def test_returns_none_for_empty(self):
        assert _text(ET.fromstring("<e></e>")) is None

    def test_returns_none_for_whitespace_only(self):
        assert _text(ET.fromstring("<e>   </e>")) is None


class TestModeValidation:
    def test_source_modes_accept_exact_active_integer_values(self, monkeypatch, tmp_path: Path):
        repo_root = _write_mode_repo(
            tmp_path,
            {
                "acceleration": "1.0",
                "gyroscope": "2",
                "magnetometer": "3.0",
                "pressure": "4",
                "temperature": "5.0",
                "light": "6",
                "analog": "9.0",
            },
        )
        monkeypatch.setattr(validate_module, "REPO_ROOT", repo_root)
        assert _load_expected_modes() == []

    @pytest.mark.parametrize("bad_value", ["1.1", "7", "nan"])
    def test_source_modes_reject_non_active_integer_values(
        self, monkeypatch, tmp_path: Path, bad_value: str
    ):
        repo_root = _write_mode_repo(
            tmp_path,
            {
                "acceleration": bad_value,
                "gyroscope": "2",
                "magnetometer": "3",
                "pressure": "4",
                "temperature": "5",
                "light": "6",
                "analog": "9",
            },
        )
        monkeypatch.setattr(validate_module, "REPO_ROOT", repo_root)
        errors = _load_expected_modes()
        assert any("must be an active integer mode ID" in error.message for error in errors)


class TestValidationError:
    def test_is_frozen(self):
        error = ValidationError("test")
        with pytest.raises(AttributeError):
            error.message = "changed"

    def test_message_stored(self):
        assert ValidationError("hello").message == "hello"
