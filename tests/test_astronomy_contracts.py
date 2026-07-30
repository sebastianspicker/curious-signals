"""Contracts for the hand-maintained astronomy experiments."""

from __future__ import annotations

from pathlib import Path

from defusedxml import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[1]
ASTRO_DIR = REPO_ROOT / "experiments" / "astronomy"
DOCS_PATH = REPO_ROOT / "docs" / "ASTRONOMY_EXPERIMENTS_COMPANION.md"

EXPECTED_FILES = {
    "albedo.phyphox",
    "greenhouse.phyphox",
    "ir-dist_habitable.phyphox",
    "missiontomars.phyphox",
    "owon_digital_multimeter-debug.phyphox",
    "pt-star.phyphox",
    "tidal-locking.phyphox",
    "transitmethode.phyphox",
}


def _text(name: str) -> str:
    return (ASTRO_DIR / name).read_text(encoding="utf-8")


def _root(name: str) -> ET.Element:
    return ET.fromstring(_text(name))


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


def test_astronomy_inventory_is_consolidated() -> None:
    assert {path.name for path in ASTRO_DIR.glob("*.phyphox")} == EXPECTED_FILES


def test_all_astronomy_files_default_to_english_with_german_and_french_support() -> None:
    for name in EXPECTED_FILES:
        root = _root(name)
        assert root.attrib.get("locale") == "en"
        locales = {
            translation.attrib["locale"]
            for translations in root.findall("translations")
            for translation in translations.findall("translation")
        }
        assert {"de", "fr"}.issubset(locales)


def test_albedo_is_bounded_as_a_reflectance_proxy() -> None:
    text = _text("albedo.phyphox").lower()
    assert text.count('<sensor type="light">') == 1
    assert text.count("<bluetooth") == 1
    assert "tba." not in text
    assert "<title>reflectivity and albedo</title>" not in text
    assert "phone light sensor" in text
    assert "ti sensortag" in text
    assert "reflectance proxy" in text


def test_habitable_zone_file_is_explicitly_qualitative() -> None:
    text = _text("ir-dist_habitable.phyphox").lower()
    assert "radation" not in text
    assert "radiation" in text
    assert "qualitative classroom analogue" in text
    assert "not a quantitative habitable-zone calculator" in text
    assert "log(t/°c)" not in text
    assert "log-log" not in text
    assert "ir-intensity" not in text
    assert "ir temperature signal" in text
    assert '<graph label="temperature"' not in text


def test_pt_star_text_is_cleaned_up() -> None:
    text = _text("pt-star.phyphox").lower()
    assert "Maxium" not in text
    assert "homeschooling" not in text
    assert "analogy" in text
    assert "does not reproduce astrophysical star formation directly" in text
    assert "does not model star formation directly" in text
    assert "which quantity changes first" in text
    assert "analogy comparison" in text


def test_mission_to_mars_supports_both_pressure_paths() -> None:
    text = _text("missiontomars.phyphox").lower()
    assert text.count('<sensor type="pressure">') == 1
    assert text.count("<bluetooth") == 1
    assert "classroom model" in text
    assert "phone pressure sensor" in text
    assert "ti sensortag" in text
    assert "altitude sickness" not in text
    assert "<title>die reise zum mars</title>" not in text
    assert "<title>checking a spaceship atmosphere</title>" in text
    assert "<title>checking a spaceship atmosphere</title>" in text
    assert '<translation locale="de">' in text
    assert '<translation locale="fr">' in text


def test_greenhouse_and_tidal_locking_are_single_files_with_clear_scope() -> None:
    greenhouse_text = _text("greenhouse.phyphox")
    greenhouse = greenhouse_text.lower()
    assert "classroom analogue" in greenhouse
    assert "one or two sensortags" in greenhouse
    assert "single setup" in greenhouse_text
    assert "comparison" in greenhouse_text
    assert "Temperature 1 (°C)" in greenhouse_text
    assert "Temperature 2 (°C)" in greenhouse_text

    tidal = _text("tidal-locking.phyphox").lower()
    assert "classroom analogue for tidal locking" in tidal
    assert "Ambient Temperature" in _text("tidal-locking.phyphox")
    assert "IR Temperature" in _text("tidal-locking.phyphox")
    assert "Object Temperature" in _text("tidal-locking.phyphox")
    assert "2in1" not in tidal
    assert "combined comparison" in tidal


def test_debug_multimeter_is_marked_as_auxiliary() -> None:
    text = _text("owon_digital_multimeter-debug.phyphox").lower()
    assert "debug utility" in text
    assert "not an astronomy teaching experiment" in text


def test_transit_method_is_single_file_and_multisource() -> None:
    text = _text("transitmethode.phyphox")
    lower = text.lower()
    assert "berets" not in lower
    assert "transit light curve" in lower or "transitlichtkurve" in lower
    assert text.count('<sensor type="light">') == 1
    assert text.count("<bluetooth") == 2
    assert "smartphone light sensor" in lower
    assert "ti sensortag" in lower
    assert "solar cell" in lower
    assert "Relative Signal" in text
    assert "[1]^3/[2]^3*100" not in text
    assert "Dirtter Transit" not in text
    assert "Third transit" in text
    assert "näherungsweie" not in text
    assert "approximated from the luminosity and temperature of the star" in lower
    assert "0.000077%" not in text
    assert "about 0.92% of the Sun" in text
    assert '<translation locale="de">' in text
    assert '<translation locale="fr">' in text


def test_tidal_locking_ambient_graphs_use_ambient_containers() -> None:
    root = _root("tidal-locking.phyphox")
    ir_view = _view(root, "IR")
    ambient_graphs = _graphs(ir_view, "Ambient Temperature")

    assert len(ambient_graphs) == 2
    assert _graph_inputs(ambient_graphs[0]) == ["t1", "ambCal1"]
    assert _graph_inputs(ambient_graphs[1]) == ["t1", "ambCal2"]


def test_tidal_locking_time_units_are_consistent() -> None:
    root = _root("tidal-locking.phyphox")

    for view_label in ("Temperature", "IR", "Light"):
        for graph in _view(root, view_label).findall("graph"):
            assert graph.attrib.get("unitX") == "s"

    export = root.find("export")
    assert export is not None
    for data in export.findall("./set/data"):
        if data.attrib.get("name", "").startswith("Time ("):
            assert data.attrib["name"] == "Time (s)"


def test_mission_to_mars_labels_match_pressure_range_quantity() -> None:
    root = _root("missiontomars.phyphox")
    text = _text("missiontomars.phyphox").lower()

    assert "pressure drop" not in text
    assert "pressure range" in text

    labels = [value.attrib.get("label") for value in root.findall("./views/view/value")]
    assert "Pressure range" in labels


def test_transit_method_star_radius_input_is_positive_only() -> None:
    root = _root("transitmethode.phyphox")
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
