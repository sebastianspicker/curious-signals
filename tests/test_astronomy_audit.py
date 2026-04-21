"""Audit contracts for the consolidated astronomy experiment subtree."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

ASTRO_DIR = Path(__file__).resolve().parents[1] / "experiments" / "astronomy"

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
