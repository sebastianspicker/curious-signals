"""Semantic XML tests for astronomy experiments."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ASTRO_DIR = REPO_ROOT / "experiments" / "astronomy"
DOCS_PATH = REPO_ROOT / "docs" / "ASTRONOMY_EXPERIMENTS_COMPANION.md"


def _load(name: str) -> ET.Element:
    return ET.parse(ASTRO_DIR / name).getroot()


def _view(root: ET.Element, label: str) -> ET.Element:
    views = root.find("views")
    assert views is not None
    for view in views.findall("view"):
        if view.attrib.get("label") == label:
            return view
    raise AssertionError(f"missing view {label!r}")


def _graphs(view: ET.Element, label: str) -> list[ET.Element]:
    return [graph for graph in view.findall("graph") if graph.attrib.get("label") == label]


def _graph_inputs(graph: ET.Element) -> list[str]:
    return [element.text.strip() for element in graph.findall("input") if element.text]


def test_tidal_locking_ambient_graphs_use_ambient_containers() -> None:
    root = _load("tidal-locking.phyphox")
    ir_view = _view(root, "IR")
    ambient_graphs = _graphs(ir_view, "Ambient Temperature")

    assert len(ambient_graphs) == 2
    assert _graph_inputs(ambient_graphs[0]) == ["t1", "ambCal1"]
    assert _graph_inputs(ambient_graphs[1]) == ["t1", "ambCal2"]


def test_tidal_locking_time_units_are_consistent() -> None:
    root = _load("tidal-locking.phyphox")

    for view_label in ("Temperature", "IR", "Light"):
        for graph in _view(root, view_label).findall("graph"):
            assert graph.attrib.get("unitX") == "s"

    export = root.find("export")
    assert export is not None
    for data in export.findall("./set/data"):
        if data.attrib.get("name", "").startswith("Time ("):
            assert data.attrib["name"] == "Time (s)"


def test_mission_to_mars_labels_match_pressure_range_quantity() -> None:
    root = _load("missiontomars.phyphox")
    text = (ASTRO_DIR / "missiontomars.phyphox").read_text(encoding="utf-8").lower()

    assert "pressure drop" not in text
    assert "pressure range" in text

    labels = [value.attrib.get("label") for value in root.findall("./views/view/value")]
    assert "Pressure range" in labels


def test_transit_method_star_radius_input_is_positive_only() -> None:
    root = _load("transitmethode.phyphox")
    planet_size_view = _view(root, "Planet Size")
    edit = planet_size_view.find("edit")

    assert edit is not None
    assert edit.attrib.get("label") == "Star radius"
    assert edit.attrib.get("signed") == "false"
    assert float(edit.attrib.get("default", "0")) > 0
    assert float(edit.attrib.get("min", "0")) > 0


def test_astronomy_companion_matches_current_wording() -> None:
    text = DOCS_PATH.read_text(encoding="utf-8").lower()

    assert "pressure range" in text
    assert "pressure drop" not in text
    assert "reflectance proxy" in text
