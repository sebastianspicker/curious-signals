"""Regression tests for repository guardrails and shared contracts."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import validate_phyphox
from defusedxml import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[1]
CONSTANTS_PATH = REPO_ROOT / "experiments" / "phyphox_constants.json"
SKETCH_PATH = REPO_ROOT / "arduino" / "phyphox_ble_sense" / "phyphox_ble_sense.ino"
LOCAL_MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def test_service_uuid_matches_between_constants_and_firmware() -> None:
    constants = json.loads(CONSTANTS_PATH.read_text(encoding="utf-8"))
    firmware = SKETCH_PATH.read_text(encoding="utf-8")

    assert constants["bluetooth"]["service_uuid"] in firmware


def test_uuid_loader_requires_all_expected_keys(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    constants_dir = repo_root / "experiments"
    sketch_dir = repo_root / "arduino" / "phyphox_ble_sense"
    constants_dir.mkdir(parents=True)
    sketch_dir.mkdir(parents=True)

    (constants_dir / "phyphox_constants.json").write_text(
        json.dumps(
            {
                "bluetooth": {
                    "data_char_uuid": "cddf1002-30f7-4671-8b43-5e40ba53514a",
                    "config_char_uuid": "cddf1003-30f7-4671-8b43-5e40ba53514a",
                }
            }
        ),
        encoding="utf-8",
    )
    (sketch_dir / "phyphox_ble_sense.ino").write_text(
        "\n".join(
            [
                (
                    "constexpr const char* kPhyphoxServiceUuid = "
                    '"cddf0001-30f7-4671-8b43-5e40ba53514a";'
                ),
                'constexpr const char* kDataCharUuid = "cddf1002-30f7-4671-8b43-5e40ba53514a";',
                'constexpr const char* kConfigCharUuid = "cddf1003-30f7-4671-8b43-5e40ba53514a";',
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(validate_phyphox, "REPO_ROOT", repo_root)

    service_uuid, data_uuid, config_uuid, errors = validate_phyphox._load_expected_uuids()

    assert service_uuid == "cddf0001-30f7-4671-8b43-5e40ba53514a"
    assert data_uuid == "cddf1002-30f7-4671-8b43-5e40ba53514a"
    assert config_uuid == "cddf1003-30f7-4671-8b43-5e40ba53514a"
    assert any("missing required bluetooth.service_uuid" in error.message for error in errors)


def test_constants_json_documents_reserved_modes() -> None:
    constants = json.loads(CONSTANTS_PATH.read_text(encoding="utf-8"))

    assert "reserved_modes" in constants, "phyphox_constants.json must have a 'reserved_modes' key"

    reserved = constants["reserved_modes"]
    assert isinstance(reserved, list), "'reserved_modes' must be a list"
    assert all(isinstance(m, int) for m in reserved), "'reserved_modes' entries must be ints"

    active_modes = set(constants.get("modes", {}).values())
    for m in reserved:
        assert 1 <= m <= 9, f"reserved mode {m} is outside the expected 1..9 range"
        assert m not in active_modes, (
            f"mode {m} appears in both 'modes' and 'reserved_modes'; "
            "a mode cannot be active and reserved at the same time"
        )


def test_firmware_initial_config_matches_default_mode() -> None:
    firmware = SKETCH_PATH.read_text(encoding="utf-8")

    assert "Mode mode = Mode::kAcceleration;" in firmware
    assert firmware.count("writeActiveModeToConfigCharacteristic();") >= 2
    assert "writeFloat32LE(configValue, sizeof(configValue), 0" in firmware


def test_firmware_bounds_config_conversion_and_reports_active_mode() -> None:
    firmware = SKETCH_PATH.read_text(encoding="utf-8")

    range_check = "configValue < 0.5f || configValue >= 9.5f"
    assert range_check in firmware
    assert firmware.index(range_check) < firmware.index("roundf(configValue)")
    assert "bytesRead == static_cast<int>(sizeof(buf))" in firmware
    assert "findSupportedMode(raw, supportedMode)" in firmware


def test_local_markdown_links_resolve() -> None:
    excluded_roots = {
        ".codacy",
        ".codegraph",
        ".git",
        ".internal",
        ".pytest_cache",
        ".ruff_cache",
        ".serena",
        "reference",
    }
    broken: list[str] = []

    for path in sorted(REPO_ROOT.rglob("*.md")):
        relative_path = path.relative_to(REPO_ROOT)
        if relative_path.parts[0] in excluded_roots:
            continue
        for raw_target in LOCAL_MARKDOWN_LINK.findall(path.read_text(encoding="utf-8")):
            target = raw_target.strip("<>").split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if not (path.parent / target).resolve().exists():
                broken.append(f"{relative_path}: {raw_target}")

    assert broken == []


def test_embedded_icons_are_valid_png_images() -> None:
    experiment_paths = sorted((REPO_ROOT / "src" / "phyphox").glob("*.phyphox.xml"))
    experiment_paths.extend(sorted((REPO_ROOT / "experiments" / "astronomy").glob("*.phyphox")))
    icons: list[tuple[Path, ET.Element]] = []

    for path in experiment_paths:
        root = ET.parse(path).getroot()
        icons.extend((path, icon) for icon in root.findall("icon"))

    assert len(icons) == 9
    for path, icon in icons:
        assert icon.attrib.get("format") == "base64", path
        image = base64.b64decode(icon.text or "", validate=True)
        assert image.startswith(b"\x89PNG\r\n\x1a\n"), path
