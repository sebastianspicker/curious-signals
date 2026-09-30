from __future__ import annotations

from defusedxml import ElementTree as ET

from curious_signals.phyphox_xml import check_core_experiment
from curious_signals.protocol import load_protocol
from tests.conftest import CONTRACT_PATH, CORE_ARTIFACT_DIR

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
    protocol = load_protocol(CONTRACT_PATH)
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
        mode_id = protocol.mode_id_for(path.name)
        assert mode_id is not None
        assert check_core_experiment(path, protocol, expected_mode=mode_id) == []


def test_core_exports_keep_device_time_and_measurement_channels() -> None:
    for path in CORE_ARTIFACT_DIR.glob("*.phyphox"):
        root = ET.parse(path).getroot()
        exports = {
            data.text.strip().removesuffix("_norm")
            for data in root.findall("./export/set/data")
            if data.text
        }

        assert exports == EXPECTED_EXPORTED_CHANNELS[path.name]


def test_measurement_labels_stay_attached_to_the_correct_channels() -> None:
    value_labels = {
        "accelerometer": {
            "Accelerometer x": "CH2_norm",
            "Accelerometer y": "CH3_norm",
            "Accelerometer z": "CH4_norm",
            "Absolute acceleration": "CH5_norm",
        },
        "gyroscope": {
            "Gyroscope x": "CH2_norm",
            "Gyroscope y": "CH3_norm",
            "Gyroscope z": "CH4_norm",
            "Absolute angular velocity": "CH5_norm",
            "Absolute": "CH5_norm",
        },
        "magnetometer": {
            "Magnetometer x": "CH2",
            "Magnetometer y": "CH3",
            "Magnetometer z": "CH4",
            "Absolute magnetic field": "CH5",
        },
        "pressure": {"Pressure": "CH2_norm"},
        "temperature": {"Temperature": "CH2", "Humidity": "CH3"},
        "light": {"Ambient": "CH2", "Red": "CH3", "Green": "CH4", "Blue": "CH5"},
        "analog_input": {
            "Voltage at A0": "CH2_norm",
            "Voltage at A1": "CH3_norm",
            "Voltage at A2": "CH4_norm",
        },
    }
    export_labels = {
        "accelerometer": [
            "Acceleration x",
            "Acceleration y",
            "Acceleration z",
            "Absolute Acceleration",
        ],
        "gyroscope": [
            "Angular Velocity x",
            "Angular Velocity y",
            "Angular Velocity z",
            "Absolute Angular Velocity",
        ],
        "magnetometer": [
            "Magnetometer x",
            "Magnetometer y",
            "Magnetometer z",
            "Absolute magnetic field",
        ],
        "pressure": ["Pressure"],
        "temperature": ["Temperature", "relative Humidity"],
        "light": ["Relative light level", "Red", "Green", "Blue"],
        "analog_input": ["Voltage at A0", "Voltage at A1", "Voltage at A2"],
    }
    for name, expected in value_labels.items():
        root = ET.parse(CORE_ARTIFACT_DIR / f"{name}_plot_v1-2.phyphox").getroot()
        values = root.findall("./views/view/value")
        assert {value.attrib["label"] for value in values} == set(expected)
        for value in values:
            assert value.findtext("input") == expected[value.attrib["label"]]
        exports = root.findall("./export/set/data")
        for channel, label in enumerate(export_labels[name], start=2):
            matches = [item for item in exports if item.attrib["name"].startswith(f"{label} (")]
            assert matches
            assert all(item.text.removesuffix("_norm") == f"CH{channel}" for item in matches)
