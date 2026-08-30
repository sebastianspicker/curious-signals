from __future__ import annotations

from defusedxml import ElementTree as ET

from curious_signals.xml_contracts import validate_phyphox
from tests.conftest import CORE_ARTIFACT_DIR

EXPECTED_MODES = {
    "accelerometer_plot_v1-2.phyphox": ("1.0", "m/s²"),
    "gyroscope_plot_v1-2.phyphox": ("2.0", "rad/s"),
    "magnetometer_plot_v1-2.phyphox": ("3.0", "µT"),
    "pressure_plot_v1-2.phyphox": ("4.0", "hPa"),
    "temperature_plot_v1-2.phyphox": ("5.0", "°C"),
    "light_plot_v1-2.phyphox": ("6.0", "a.u."),
    "analog_input_plot_v1-2.phyphox": ("9.0", "mV"),
}

EXPECTED_EXPORTED_CHANNELS = {
    "accelerometer_plot_v1-2.phyphox": {"CH1", "CH2", "CH3", "CH4", "CH5"},
    "gyroscope_plot_v1-2.phyphox": {"CH1", "CH2", "CH3", "CH4", "CH5"},
    "magnetometer_plot_v1-2.phyphox": {"CH1", "CH2", "CH3", "CH4", "CH5"},
    "pressure_plot_v1-2.phyphox": {"CH1", "CH2"},
    "temperature_plot_v1-2.phyphox": {"CH1", "CH2", "CH3"},
    "light_plot_v1-2.phyphox": {"CH1", "CH2", "CH3", "CH4", "CH5"},
    "analog_input_plot_v1-2.phyphox": {"CH1", "CH2", "CH3", "CH4"},
}


def test_core_inventory_validates_and_declares_mode_config_and_classroom_units() -> None:
    paths = sorted(CORE_ARTIFACT_DIR.glob("*.phyphox"))

    assert {path.name for path in paths} == set(EXPECTED_MODES)
    for path in paths:
        root = ET.parse(path).getroot()
        config = root.find("./output/bluetooth/config")
        assert config is not None and config.text is not None
        assert config.text.strip() == EXPECTED_MODES[path.name][0]
        assert config.attrib.get("conversion") == "float32LittleEndian"
        assert any(
            value.attrib.get("unit") == EXPECTED_MODES[path.name][1]
            for value in root.findall(".//value")
        )
        assert validate_phyphox(path) == []


def test_core_exports_keep_app_managed_time_and_measurement_channels() -> None:
    for path in CORE_ARTIFACT_DIR.glob("*.phyphox"):
        root = ET.parse(path).getroot()
        exports = {
            data.text.strip().removesuffix("_norm")
            for data in root.findall("./export/set/data")
            if data.text
        }

        assert exports == EXPECTED_EXPORTED_CHANNELS[path.name]
