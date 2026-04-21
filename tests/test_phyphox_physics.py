"""Physics-oriented tests for the phyphox classroom experiments."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPO_ROOT / "src" / "phyphox"
SKETCH_PATH = REPO_ROOT / "arduino" / "phyphox_ble_sense" / "phyphox_ble_sense.ino"


def _load(path: Path) -> ET.Element:
    return ET.parse(path).getroot()


def _view(root: ET.Element, label: str) -> ET.Element:
    views = root.find("views")
    assert views is not None
    for view in views.findall("view"):
        if view.attrib.get("label") == label:
            return view
    raise AssertionError(f"missing view {label!r}")


def _graph(view: ET.Element, label: str) -> ET.Element:
    for graph in view.findall("graph"):
        if graph.attrib.get("label") == label:
            return graph
    raise AssertionError(f"missing graph {label!r}")


def _value(view: ET.Element, label: str) -> ET.Element:
    for value in view.findall("value"):
        if value.attrib.get("label") == label:
            return value
    raise AssertionError(f"missing value {label!r}")


def _analysis_formulas(root: ET.Element) -> list[str]:
    analysis = root.find("analysis")
    if analysis is None:
        return []
    return [formula.attrib.get("formula", "") for formula in analysis.findall("formula")]


def _export_set(root: ET.Element, name: str) -> ET.Element:
    export = root.find("export")
    assert export is not None
    for item in export.findall("set"):
        if item.attrib.get("name") == name:
            return item
    raise AssertionError(f"missing export set {name!r}")


def _data_names(export_set: ET.Element) -> list[str]:
    return [data.attrib["name"] for data in export_set.findall("data")]


def test_accelerometer_physics_contract() -> None:
    root = _load(SOURCE_DIR / "accelerometer_plot_v1-2.phyphox.xml")
    assert root.findtext("./output/bluetooth/config") == "1.0"
    assert _analysis_formulas(root) == ["[1_]*9.81"] * 4

    graph_view = _view(root, "Graph")
    absolute_view = _view(root, "Absolute")
    raw_view = _view(root, "Raw Data")
    for axis in ("x", "y", "z"):
        assert _graph(graph_view, f"Accelerometer {axis}").attrib["unitY"] == "m/s²"
        assert _graph(raw_view, f"Accelerometer {axis}").attrib["unitY"] == "g"
    assert _graph(absolute_view, "Absolute acceleration").attrib["unitY"] == "m/s²"
    assert _graph(raw_view, "Absolute acceleration").attrib["unitY"] == "g"

    export_set = _export_set(root, "Raw data (m/s²)")
    assert _data_names(export_set) == [
        "Time t (s)",
        "Acceleration x (m/s²)",
        "Acceleration y (m/s²)",
        "Acceleration z (m/s²)",
        "Absolute Acceleration (m/s²)",
    ]


def test_gyroscope_physics_contract() -> None:
    root = _load(SOURCE_DIR / "gyroscope_plot_v1-2.phyphox.xml")
    assert root.findtext("./output/bluetooth/config") == "2.0"
    assert _analysis_formulas(root) == ["[1_]*3.14159/180"] * 4

    graph_view = _view(root, "Graph")
    absolute_view = _view(root, "Absolute")
    raw_view = _view(root, "Raw Data")
    for axis in ("x", "y", "z"):
        assert _graph(graph_view, f"Gyroscope {axis}").attrib["unitY"] == "rad/s"
        assert _graph(raw_view, f"Gyroscope {axis}").attrib["unitY"] == "deg/s"
    assert _graph(absolute_view, "Absolute angular velocity").attrib["unitY"] == "rad/s"
    assert _graph(raw_view, "Absolute").attrib["unitY"] == "deg/s"


def test_magnetometer_physics_contract() -> None:
    root = _load(SOURCE_DIR / "magnetometer_plot_v1-2.phyphox.xml")
    assert root.findtext("./output/bluetooth/config") == "3.0"
    assert _analysis_formulas(root) == []

    graph_view = _view(root, "Graph")
    absolute_view = _view(root, "Absolute")
    multi_view = _view(root, "Multi")
    simple_view = _view(root, "Simple")
    for axis in ("x", "y", "z"):
        assert _graph(graph_view, f"Magnetometer {axis}").attrib["unitY"] == "µT"
        assert _value(multi_view, f"Magnetometer {axis}").attrib["unit"] == "µT"
        assert _value(simple_view, f"Magnetometer {axis}").attrib["unit"] == "µT"
    assert _graph(absolute_view, "Absolute magnetic field").attrib["unitY"] == "µT"
    assert _value(absolute_view, "Absolute magnetic field").attrib["unit"] == "µT"


def test_pressure_physics_contract() -> None:
    root = _load(SOURCE_DIR / "pressure_plot_v1-2.phyphox.xml")
    assert root.findtext("./output/bluetooth/config") == "4.0"
    assert _analysis_formulas(root) == ["[1_]*10"]

    graph_view = _view(root, "Graph")
    raw_view = _view(root, "Raw Data")
    simple_view = _view(root, "Simple")
    assert _graph(graph_view, "Pressure").attrib["unitY"] == "hPa"
    assert _graph(raw_view, "Pressure").attrib["unitY"] == "kPa"
    assert _value(simple_view, "Pressure").attrib["unit"] == "hPa"

    export_set = _export_set(root, "Raw data (hPa)")
    assert _data_names(export_set) == ["Time t (s)", "Pressure (hPa)"]


def test_temperature_physics_contract() -> None:
    root = _load(SOURCE_DIR / "temperature_plot_v1-2.phyphox.xml")
    assert root.findtext("./output/bluetooth/config") == "5.0"
    assert _analysis_formulas(root) == []

    graph_view = _view(root, "Graph")
    assert _graph(graph_view, "Temperature").attrib["unitY"] == "°C"
    assert _graph(graph_view, "Humidity").attrib["unitY"] == "%"

    export_set = _export_set(root, "Raw data")
    assert _data_names(export_set) == [
        "Time t (s)",
        "Temperature (°C)",
        "relative Humidity (%)",
    ]


def test_light_physics_contract() -> None:
    root = _load(SOURCE_DIR / "light_plot_v1-2.phyphox.xml")
    sketch_text = SKETCH_PATH.read_text(encoding="utf-8")
    assert root.findtext("./output/bluetooth/config") == "6.0"
    assert _analysis_formulas(root) == []
    assert "ch2 > 4.0f" not in sketch_text

    graph_view = _view(root, "Graph")
    ambient_view = _view(root, "Ambient")
    simple_view = _view(root, "Simple")
    assert _graph(graph_view, "Relative Light Level").attrib["unitY"] == "a.u."
    assert _graph(graph_view, "Relative Light Level").attrib["labelY"] == "counts"
    assert _graph(ambient_view, "Ambient").attrib["unitY"] == "a.u."
    assert _value(simple_view, "Ambient").attrib["unit"] == "a.u."
    assert "caps ambient (CH2) at 4.0" not in (
        SOURCE_DIR / "light_plot_v1-2.phyphox.xml"
    ).read_text(encoding="utf-8")

    export_set = _export_set(root, "Raw data")
    assert _data_names(export_set) == [
        "Time t (s)",
        "Relative light level (a.u.)",
        "Red (a.u.)",
        "Green (a.u.)",
        "Blue (a.u.)",
    ]


def test_analog_input_physics_contract() -> None:
    root = _load(SOURCE_DIR / "analog_input_plot_v1-2.phyphox.xml")
    assert root.findtext("./output/bluetooth/config") == "9.0"
    assert _analysis_formulas(root) == ["[1_]*3.226"] * 3

    graph_view = _view(root, "Graph")
    raw_view = _view(root, "Raw Data")
    simple_view = _view(root, "Simple")
    for channel in ("A0", "A1", "A2"):
        assert _graph(graph_view, f"Voltage at {channel}").attrib["unitY"] == "mV"
        assert _value(simple_view, f"Voltage at {channel}").attrib["unit"] == "mV"
        assert _graph(raw_view, f"Analog Input {channel}").attrib["unitY"] == ""

    export_set = _export_set(root, "Raw data (ADC readings)")
    assert _data_names(export_set) == [
        "Time t (s)",
        "Analog Input A0",
        "Analog Input A1",
        "Analog Input A2",
    ]
