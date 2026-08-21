#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException
from phyphox_xml_contracts import ValidationError, validate_phyphox

REPO_ROOT = Path(__file__).resolve().parent.parent
SKETCH_UUID_RE = re.compile(
    (
        r"^constexpr const char\*\s+"
        r'(kPhyphoxServiceUuid|kDataCharUuid|kConfigCharUuid)\s*=\s*"([^"]+)";'
    )
)
MODE_ID_RE = re.compile(r"^\s*k([A-Za-z0-9]+)\s*=\s*(\d+),?$")
SKETCH_UUID_KEYS = {
    "kPhyphoxServiceUuid": "service",
    "kDataCharUuid": "data",
    "kConfigCharUuid": "config",
}
REQUIRED_SKETCH_UUIDS = {
    "service": "kPhyphoxServiceUuid",
    "data": "kDataCharUuid",
    "config": "kConfigCharUuid",
}
MODE_NAME_MAP = {
    "Acceleration": "acceleration",
    "Gyroscope": "gyroscope",
    "Magnetometer": "magnetometer",
    "Pressure": "pressure",
    "TemperatureHumidity": "temperature_humidity",
    "LightRgb": "light_rgb",
    "AnalogInputs": "analog_inputs",
}


def _read_constants_uuids(
    constants_path: Path,
) -> tuple[str | None, str | None, str | None, list[ValidationError]]:
    errors: list[ValidationError] = []
    try:
        constants = json.loads(constants_path.read_text(encoding="utf-8"))
    except OSError as error:
        return None, None, None, [ValidationError(f"{constants_path}: cannot read file: {error}")]
    except json.JSONDecodeError as error:
        return None, None, None, [ValidationError(f"{constants_path}: invalid JSON: {error}")]
    bluetooth = constants.get("bluetooth", {})
    service_uuid = bluetooth.get("service_uuid")
    data_uuid = bluetooth.get("data_char_uuid")
    config_uuid = bluetooth.get("config_char_uuid")
    for key in ("service_uuid", "data_char_uuid", "config_char_uuid"):
        if not bluetooth.get(key):
            errors.append(ValidationError(f"{constants_path}: missing required bluetooth.{key}"))
    return service_uuid, data_uuid, config_uuid, errors


def _read_sketch_uuids(
    sketch_path: Path,
) -> tuple[str | None, str | None, str | None, list[ValidationError]]:
    uuids: dict[str, str | None] = dict.fromkeys(REQUIRED_SKETCH_UUIDS, None)
    errors: list[ValidationError] = []
    try:
        for line in sketch_path.read_text(encoding="utf-8").splitlines():
            match = SKETCH_UUID_RE.match(line.strip())
            if match:
                key, value = match.groups()
                uuids[SKETCH_UUID_KEYS[key]] = value
    except OSError as error:
        return None, None, None, [ValidationError(f"{sketch_path}: cannot read file: {error}")]
    for uuid_key, sketch_name in REQUIRED_SKETCH_UUIDS.items():
        if not uuids[uuid_key]:
            errors.append(ValidationError(f"{sketch_path}: missing required {sketch_name}"))
    return uuids["service"], uuids["data"], uuids["config"], errors


def _uuid_mismatch_errors(
    constants_path: Path,
    sketch_path: Path,
    constants_uuids: tuple[str | None, str | None, str | None],
    sketch_uuids: tuple[str | None, str | None, str | None],
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for name, constants_uuid, sketch_uuid in zip(
        ("service_uuid", "data_char_uuid", "config_char_uuid"),
        constants_uuids,
        sketch_uuids,
        strict=True,
    ):
        if constants_uuid and sketch_uuid and constants_uuid != sketch_uuid:
            errors.append(ValidationError(f"{constants_path}: {name} does not match {sketch_path}"))
    return errors


def _load_expected_uuids() -> tuple[str | None, str | None, str | None, list[ValidationError]]:
    constants_path = REPO_ROOT / "experiments" / "phyphox_constants.json"
    sketch_path = REPO_ROOT / "arduino" / "phyphox_ble_sense" / "phyphox_ble_sense.ino"
    constants_uuids = _read_constants_uuids(constants_path)
    sketch_uuids = _read_sketch_uuids(sketch_path)
    errors = [*constants_uuids[3], *sketch_uuids[3]]
    errors.extend(
        _uuid_mismatch_errors(constants_path, sketch_path, constants_uuids[:3], sketch_uuids[:3])
    )
    constants_service_uuid, constants_data_uuid, constants_config_uuid = constants_uuids[:3]
    sketch_service_uuid, sketch_data_uuid, sketch_config_uuid = sketch_uuids[:3]
    return (
        constants_service_uuid or sketch_service_uuid,
        constants_data_uuid or sketch_data_uuid,
        constants_config_uuid or sketch_config_uuid,
        errors,
    )


def _load_constants_modes(
    constants_path: Path,
) -> tuple[dict[str, int], list[ValidationError], bool]:
    errors: list[ValidationError] = []
    constants_modes: dict[str, int] = {}
    try:
        constants = json.loads(constants_path.read_text(encoding="utf-8"))
    except OSError as error:
        return (
            constants_modes,
            [ValidationError(f"{constants_path}: cannot read file: {error}")],
            False,
        )
    except json.JSONDecodeError as error:
        return constants_modes, [ValidationError(f"{constants_path}: invalid JSON: {error}")], False
    raw_modes = constants.get("modes", {})
    if not raw_modes:
        errors.append(ValidationError(f"{constants_path}: missing required modes object"))
    for name in MODE_NAME_MAP.values():
        value = raw_modes.get(name)
        if not isinstance(value, int):
            errors.append(ValidationError(f"{constants_path}: missing required modes.{name}"))
            continue
        constants_modes[name] = value
    return constants_modes, errors, True


def _iter_mode_enum_lines(sketch_text: str) -> list[str]:
    mode_lines: list[str] = []
    in_enum = False
    for line in sketch_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("enum class Mode"):
            in_enum = True
            continue
        if in_enum and stripped == "};":
            break
        if in_enum:
            mode_lines.append(stripped)
    return mode_lines


def _sketch_mode_entry(stripped: str) -> tuple[str, int] | None:
    match = MODE_ID_RE.match(stripped)
    if not match:
        return None
    raw_name, value = match.groups()
    mapped_name = MODE_NAME_MAP.get(raw_name)
    return (mapped_name, int(value)) if mapped_name else None


def _sketch_mode_values(sketch_text: str) -> dict[str, int]:
    sketch_modes: dict[str, int] = {}
    for stripped in _iter_mode_enum_lines(sketch_text):
        if entry := _sketch_mode_entry(stripped):
            name, value = entry
            sketch_modes[name] = value
    return sketch_modes


def _missing_sketch_mode_errors(
    sketch_path: Path, sketch_modes: dict[str, int]
) -> list[ValidationError]:
    return [
        ValidationError(f"{sketch_path}: missing required mode {name}")
        for name in MODE_NAME_MAP.values()
        if name not in sketch_modes
    ]


def _load_sketch_modes(sketch_path: Path) -> tuple[dict[str, int], list[ValidationError], bool]:
    try:
        sketch_modes = _sketch_mode_values(sketch_path.read_text(encoding="utf-8"))
    except OSError as error:
        return {}, [ValidationError(f"{sketch_path}: cannot read file: {error}")], False
    return sketch_modes, _missing_sketch_mode_errors(sketch_path, sketch_modes), True


def _parse_source_mode_root(path: Path) -> tuple[ET.Element | None, list[ValidationError]]:
    try:
        return ET.parse(path).getroot(), []
    except OSError as error:
        return None, [ValidationError(f"{path}: cannot parse mode config: {error}")]
    except DefusedXmlException as error:
        return None, [
            ValidationError(f"{path}: cannot parse mode config: unsafe XML rejected: {error}")
        ]
    except ET.ParseError as error:
        return None, [ValidationError(f"{path}: cannot parse mode config: {error}")]


def _source_mode_config(path: Path, root: ET.Element) -> tuple[str | None, list[ValidationError]]:
    config = root.find("./output/bluetooth/config")
    if config is None or config.text is None:
        return None, [ValidationError(f"{path}: missing output bluetooth config value")]
    return config.text.strip(), []


def _source_mode_value(
    path: Path, raw_config: str, active_mode_ids: set[int]
) -> tuple[int | None, list[ValidationError]]:
    try:
        numeric_config = float(raw_config)
    except ValueError:
        return None, [ValidationError(f"{path}: invalid output bluetooth config value")]
    if not math.isfinite(numeric_config) or not numeric_config.is_integer():
        return None, [
            ValidationError(
                f"{path}: output bluetooth config value must be an active integer mode ID"
            )
        ]
    mode_id = int(numeric_config)
    if mode_id not in active_mode_ids:
        return None, [
            ValidationError(
                f"{path}: output bluetooth config value must be an active integer mode ID"
            )
        ]
    return mode_id, []


def _source_mode_id(
    path: Path, constants_modes: dict[str, int]
) -> tuple[int | None, list[ValidationError]]:
    root, parse_errors = _parse_source_mode_root(path)
    if parse_errors:
        return None, parse_errors
    if root is None:
        return None, [ValidationError(f"{path}: cannot parse mode config: parser returned no root")]
    raw_config, config_errors = _source_mode_config(path, root)
    if config_errors:
        return None, config_errors
    if raw_config is None:
        return None, [ValidationError(f"{path}: missing output bluetooth config value")]
    return _source_mode_value(path, raw_config, set(constants_modes.values()))


def _load_source_mode_ids(
    source_dir: Path, constants_modes: dict[str, int]
) -> tuple[set[int], list[ValidationError]]:
    errors: list[ValidationError] = []
    source_mode_ids: set[int] = set()
    for path in sorted(source_dir.glob("*.phyphox.xml")):
        mode_id, mode_errors = _source_mode_id(path, constants_modes)
        errors.extend(mode_errors)
        if mode_id is not None:
            source_mode_ids.add(mode_id)
    return source_mode_ids, errors


def _load_expected_modes() -> list[ValidationError]:
    constants_path = REPO_ROOT / "experiments" / "phyphox_constants.json"
    sketch_path = REPO_ROOT / "arduino" / "phyphox_ble_sense" / "phyphox_ble_sense.ino"
    source_dir = REPO_ROOT / "src" / "phyphox"
    constants_modes, constants_errors, constants_loaded = _load_constants_modes(constants_path)
    sketch_modes, sketch_errors, sketch_loaded = _load_sketch_modes(sketch_path)
    errors = [*constants_errors, *sketch_errors]
    if not constants_loaded or not sketch_loaded:
        return errors
    source_mode_ids, source_errors = _load_source_mode_ids(source_dir, constants_modes)
    errors.extend(source_errors)
    if constants_modes and sketch_modes and constants_modes != sketch_modes:
        errors.append(ValidationError(f"{constants_path}: mode IDs do not match {sketch_path}"))
    if constants_modes and set(constants_modes.values()) != source_mode_ids:
        errors.append(
            ValidationError(f"{constants_path}: mode IDs do not match source phyphox config values")
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Plausibility checks for phyphox experiment XML.")
    ap.add_argument("paths", nargs="+", help="Path(s) to *.phyphox file(s)")
    args = ap.parse_args(argv)
    _, expected_data_uuid, expected_config_uuid, errors = _load_expected_uuids()
    errors.extend(_load_expected_modes())
    for path in args.paths:
        errors.extend(validate_phyphox(path, expected_data_uuid, expected_config_uuid))
    if errors:
        for error in errors:
            print(error.message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
