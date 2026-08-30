from __future__ import annotations

from collections import Counter

from defusedxml import ElementTree as ET

from tests.conftest import ASTRONOMY_DIR

EXPECTED = {
    "albedo.phyphox",
    "greenhouse.phyphox",
    "ir-dist_habitable.phyphox",
    "missiontomars.phyphox",
    "owon_digital_multimeter-debug.phyphox",
    "pt-star.phyphox",
    "tidal-locking.phyphox",
    "transitmethode.phyphox",
}


def declared_containers(root: ET.Element) -> set[str]:
    return {node.text.strip() for node in root.findall("./data-containers/container") if node.text}


def referenced_containers(root: ET.Element) -> set[str]:
    references: set[str] = set()
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] not in {"data", "input", "output"}:
            continue
        if node.tag.rsplit("}", 1)[-1] == "input" and node.attrib.get("type") == "value":
            continue
        if node.text and node.text.strip():
            references.add(node.text.strip())
    return references


def test_astronomy_inventory_locales_and_references_are_import_safe() -> None:
    paths = sorted(ASTRONOMY_DIR.glob("*.phyphox"))

    assert {path.name for path in paths} == EXPECTED
    for path in paths:
        root = ET.parse(path).getroot()
        containers = [
            node.text.strip() for node in root.findall("./data-containers/container") if node.text
        ]
        locales = {node.attrib.get("locale") for node in root.findall("./translations/translation")}
        assert root.attrib.get("locale") == "en"
        assert {"de", "fr"}.issubset(locales)
        assert not [name for name, count in Counter(containers).items() if count > 1]
        assert referenced_containers(root) <= declared_containers(root)


def test_astronomy_model_invariants_keep_units_and_positive_star_radius() -> None:
    mars = ET.parse(ASTRONOMY_DIR / "missiontomars.phyphox").getroot()
    tidal = ET.parse(ASTRONOMY_DIR / "tidal-locking.phyphox").getroot()
    transit = ET.parse(ASTRONOMY_DIR / "transitmethode.phyphox").getroot()

    assert any(value.attrib.get("label") == "Pressure range" for value in mars.findall(".//value"))
    views = {view.attrib.get("label"): view for view in tidal.findall("./views/view")}
    for label in ("Temperature", "IR", "Light"):
        assert all(graph.attrib.get("unitX") == "s" for graph in views[label].findall("graph"))
    star_radius = next(
        edit for edit in transit.findall(".//edit") if edit.attrib.get("label") == "Star radius"
    )
    assert star_radius.attrib.get("signed") == "false"
    assert float(star_radius.attrib["min"]) > 0
