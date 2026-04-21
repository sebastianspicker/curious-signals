"""Consolidation contracts for the astronomy experiment subtree."""

from __future__ import annotations

from pathlib import Path

ASTRO_DIR = Path(__file__).resolve().parents[1] / "experiments" / "astronomy"


def _text(name: str) -> str:
    return (ASTRO_DIR / name).read_text(encoding="utf-8")


def test_mission_to_mars_supports_phone_and_sensortag() -> None:
    text = _text("missiontomars.phyphox")
    assert text.count('<sensor type="pressure">') == 1
    assert text.count("<bluetooth") == 1
    assert "phone pressure sensor" in text.lower()
    assert "ti sensortag" in text.lower()


def test_greenhouse_single_and_comparison_live_in_one_file() -> None:
    text = _text("greenhouse.phyphox")
    assert "one or two sensortags" in text.lower()
    assert "Single setup" in text
    assert "Comparison" in text


def test_tidal_locking_keeps_the_richer_ir_and_ambient_views() -> None:
    text = _text("tidal-locking.phyphox")
    assert "Ambient Temperature" in text
    assert "IR Temperature" in text
    assert "Object Temperature" in text


def test_transit_method_combines_all_supported_measurement_paths() -> None:
    text = _text("transitmethode.phyphox")
    assert text.count('<sensor type="light">') == 1
    assert text.count("<bluetooth") == 2
    assert "smartphone light sensor" in text.lower()
    assert "ti sensortag" in text.lower()
    assert "solar cell" in text.lower()
    assert "Relative Signal" in text


def test_albedo_supports_phone_and_sensortag_in_one_file() -> None:
    text = _text("albedo.phyphox")
    assert text.count('<sensor type="light">') == 1
    assert text.count("<bluetooth") == 1
    assert "phone light sensor" in text.lower()
    assert "ti sensortag" in text.lower()
    assert "reflectance proxy" in text.lower()
