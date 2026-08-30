"""Cross-check the JSON protocol contract against firmware and core XML."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

from .contract import active_modes
from .layout import core_source_dir, firmware_path

SKETCH_UUID_RE = re.compile(
    r"^constexpr const char\*\s+"
    r'(kPhyphoxServiceUuid|kDataCharUuid|kConfigCharUuid)\s*=\s*"([^"]+)";',
    re.MULTILINE,
)
SKETCH_MODE_RE = re.compile(r"^\s*k([A-Za-z0-9]+)\s*=\s*(\d+),?$")
ADVERTISED_NAME_RE = re.compile(r'BLE\.set(Device|Local)Name\("([^"]+)"\);')
PAYLOAD_SIZE_RE = re.compile(r"constexpr int kPayloadSizeBytes = (\d+);")
SEND_PERIOD_RE = re.compile(r"constexpr unsigned long kSendPeriodMs = (\d+);")
PAYLOAD_WRITE_RE = re.compile(
    r"writeFloat32LE\(payload, sizeof\(payload\), (\d+), ([A-Za-z0-9_]+)\);"
)
MODE_NAME_MAP = {
    "Acceleration": "acceleration",
    "Gyroscope": "gyroscope",
    "Magnetometer": "magnetometer",
    "Pressure": "pressure",
    "TemperatureHumidity": "temperature_humidity",
    "LightRgb": "light_rgb",
    "AnalogInputs": "analog_inputs",
}
UUID_NAMES = {
    "kPhyphoxServiceUuid": "service_uuid",
    "kDataCharUuid": "data_char_uuid",
    "kConfigCharUuid": "config_char_uuid",
}
FIRMWARE_FIELD_VALUES = {
    "device_time_seconds": "t",
    "channel_2": "ch2",
    "channel_3": "ch3",
    "channel_4": "ch4",
    "channel_5": "ch5",
}
BLE_ACCESS = {"notify": "BLENotify", "read": "BLERead", "write": "BLEWrite"}


def _read(path: Path, label: str, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        errors.append(f"{path}: cannot read {label}: {error}")
        return None


def _firmware_values(sketch: Path, contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    text = _read(sketch, "firmware", errors)
    if text is None:
        return errors
    device = contract.get("device", {})
    expected_name = device.get("name") if isinstance(device, dict) else None
    advertised_names = {kind: value for kind, value in ADVERTISED_NAME_RE.findall(text)}
    for kind in ("Device", "Local"):
        if kind not in advertised_names:
            errors.append(f"{sketch}: missing BLE.set{kind}Name")
        elif advertised_names[kind] != expected_name:
            errors.append(f"{sketch}: BLE {kind.lower()} name does not match protocol contract")
    bluetooth = contract.get("bluetooth", {})
    expected_uuids = bluetooth if isinstance(bluetooth, dict) else {}
    found_uuids = {UUID_NAMES[key]: value for key, value in SKETCH_UUID_RE.findall(text)}
    for key in UUID_NAMES.values():
        if key not in found_uuids:
            errors.append(f"{sketch}: missing required {key}")
        elif found_uuids[key] != expected_uuids.get(key):
            errors.append(f"{sketch}: {key} does not match protocol contract")
    frame = contract.get("frame", {})
    data = frame.get("data", {}) if isinstance(frame, dict) else {}
    config = frame.get("config", {}) if isinstance(frame, dict) else {}
    payload_match = PAYLOAD_SIZE_RE.search(text)
    if payload_match is None or int(payload_match.group(1)) != data.get("byte_length"):
        errors.append(f"{sketch}: data frame size does not match protocol contract")
    period_match = SEND_PERIOD_RE.search(text)
    if period_match is None or int(period_match.group(1)) != frame.get("sample_period_ms"):
        errors.append(f"{sketch}: sample period does not match protocol contract")
    config_access = " | ".join(BLE_ACCESS.get(value, "") for value in config.get("access", []))
    config_characteristic = (
        f"BLECharacteristic configCharacteristic(kConfigCharUuid, {config_access}, "
        f"{config.get('byte_length')});"
    )
    if config_characteristic not in text:
        errors.append(f"{sketch}: config frame size does not match protocol contract")
    data_access = " | ".join(BLE_ACCESS.get(value, "") for value in data.get("access", []))
    data_characteristic = (
        f"BLECharacteristic dataCharacteristic(kDataCharUuid, {data_access}, kPayloadSizeBytes);"
    )
    if data_characteristic not in text:
        errors.append(f"{sketch}: data characteristic access does not match protocol contract")
    default_name = next(
        (
            name
            for raw_name, name in MODE_NAME_MAP.items()
            if next(
                (mode.get("id") for mode in active_modes(contract) if mode.get("name") == name),
                None,
            )
            == contract.get("modes", {}).get("default")
        ),
        None,
    )
    default_token = next(
        (raw_name for raw_name, name in MODE_NAME_MAP.items() if name == default_name), None
    )
    if default_token is None or f"Mode mode = Mode::k{default_token};" not in text:
        errors.append(f"{sketch}: default mode does not match protocol contract")
    selection = config.get("selection", {}) if isinstance(config, dict) else {}
    minimum = selection.get("minimum")
    maximum = selection.get("maximum_exclusive")
    selection_range = f"configValue < {minimum}f || configValue >= {maximum}f"
    if selection_range not in text:
        errors.append(f"{sketch}: config selection range does not match protocol contract")
    if selection.get("rounding") == "nearest_integer" and "roundf(configValue)" not in text:
        errors.append(f"{sketch}: config selection rounding does not match protocol contract")
    expected_writes = [
        (field["offset"], FIRMWARE_FIELD_VALUES.get(field["name"]))
        for field in data.get("fields", [])
    ]
    actual_writes = [(int(offset), value) for offset, value in PAYLOAD_WRITE_RE.findall(text)]
    if None in {value for _, value in expected_writes} or actual_writes != expected_writes:
        errors.append(f"{sketch}: payload writes do not match protocol field order")
    codec_snippets = (
        "buf[offset + 0] = (uint8_t)(raw & 0xFFu);",
        "buf[offset + 3] = (uint8_t)((raw >> 24) & 0xFFu);",
        "setModeFromConfig(readFloat32LE(buf, sizeof(buf)));",
        "writeFloat32LE(configValue, sizeof(configValue), 0, (float)(int)mode);",
    )
    if any(snippet not in text for snippet in codec_snippets):
        errors.append(f"{sketch}: little-endian float codec use does not match protocol contract")
    errors.extend(_firmware_mode_errors(sketch, text, contract))
    return errors


def _firmware_mode_errors(sketch: Path, text: str, contract: dict[str, Any]) -> list[str]:
    in_enum = False
    found: dict[str, int] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("enum class Mode"):
            in_enum = True
            continue
        if in_enum and stripped == "};":
            break
        if in_enum and (match := SKETCH_MODE_RE.match(stripped)):
            raw_name, raw_id = match.groups()
            if name := MODE_NAME_MAP.get(raw_name):
                found[name] = int(raw_id)
    expected = {mode["name"]: mode["id"] for mode in active_modes(contract)}
    if found != expected:
        return [f"{sketch}: mode IDs do not match protocol contract"]
    return []


def _source_mode(path: Path) -> tuple[float | None, str | None]:
    try:
        root = ET.parse(path).getroot()
    except OSError as error:
        return None, f"{path}: cannot parse mode config: {error}"
    except DefusedXmlException as error:
        return None, f"{path}: cannot parse mode config: unsafe XML rejected: {error}"
    except ET.ParseError as error:
        return None, f"{path}: cannot parse mode config: {error}"
    config = root.find("./output/bluetooth/config")
    if config is None or config.text is None:
        return None, f"{path}: missing output bluetooth config value"
    try:
        value = float(config.text.strip())
    except ValueError:
        return None, f"{path}: invalid output bluetooth config value"
    return value, None


def _source_mode_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {mode["experiment"]: mode["id"] for mode in active_modes(contract)}
    source_dir = core_source_dir()
    source_files = sorted(source_dir.glob("*.phyphox.xml"))
    actual_names = {path.name.removesuffix(".xml") for path in source_files}
    if actual_names != set(expected):
        errors.append(f"{source_dir}: source experiment filenames do not match protocol contract")
    for path in source_files:
        mode_value, error = _source_mode(path)
        if error:
            errors.append(error)
            continue
        if mode_value is None or not math.isfinite(mode_value) or not mode_value.is_integer():
            errors.append(
                f"{path}: output bluetooth config value must be an active integer mode ID"
            )
            continue
        expected_mode = expected.get(path.name.removesuffix(".xml"))
        if expected_mode is None or int(mode_value) != expected_mode:
            errors.append(f"{path}: output bluetooth config value does not match protocol contract")
    return errors


def validate_repository_contract(contract: dict[str, Any]) -> list[str]:
    """Return errors where firmware or core source XML diverge from the contract."""

    return [*_firmware_values(firmware_path(), contract), *_source_mode_errors(contract)]
