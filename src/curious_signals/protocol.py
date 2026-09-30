"""Loading, structural validation, and the typed model of the BLE protocol contract."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import ToolError

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
MODE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
TYPE_WIDTHS = {"float32": 4}
WIRE_ENCODING = "float32LittleEndian"
DATA_ACCESS = {"notify"}
CONFIG_ACCESS = {"read", "write"}


@dataclass(frozen=True)
class Mode:
    id: int
    name: str
    experiment: str
    channels: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class Protocol:
    device_name: str
    service_uuid: str
    data_char_uuid: str
    config_char_uuid: str
    sample_period_ms: int
    data_encoding: str
    data_offsets: tuple[int, ...]
    config_encoding: str
    default_mode: int
    modes: tuple[Mode, ...]
    reserved_modes: tuple[int, ...]

    @property
    def experiments(self) -> tuple[str, ...]:
        return tuple(mode.experiment for mode in self.modes)

    def mode_for_experiment(self, filename: str) -> Mode | None:
        """Return the active mode whose generated experiment has this filename."""

        return next((mode for mode in self.modes if mode.experiment == filename), None)


def read_contract(path: Path) -> object:
    """Read the raw JSON contract, raising ToolError when it cannot be read or parsed."""

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ToolError(f"{path}: cannot read contract: {error}") from error
    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        raise ToolError(f"{path}: invalid JSON: {error}") from error


def _mapping(value: object, location: str, errors: list[str]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    errors.append(f"contract: {location} must be an object")
    return {}


def _required_string(mapping: dict[str, Any], key: str, location: str, errors: list[str]) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        errors.append(f"contract: {location}.{key} must be a non-empty string")
        return ""
    return value


def _integer(
    value: object, location: str, errors: list[str], *, positive: bool = False
) -> int | None:
    if not isinstance(value, int) or isinstance(value, bool) or (positive and value <= 0):
        qualifier = "a positive integer" if positive else "an integer"
        errors.append(f"contract: {location} must be {qualifier}")
        return None
    return value


def _number(value: object, location: str, errors: list[str]) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        errors.append(f"contract: {location} must be a finite number")
        return None
    return float(value)


def _string_list(value: object, location: str, errors: list[str]) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        errors.append(f"contract: {location} must be a non-empty list of strings")
        return []
    if len(value) != len(set(value)):
        errors.append(f"contract: {location} entries must be unique")
    return value


def _required_choice(
    mapping: dict[str, Any], key: str, location: str, allowed: set[str], errors: list[str]
) -> str:
    value = _required_string(mapping, key, location, errors)
    if value and value not in allowed:
        errors.append(f"contract: {location}.{key} must be one of {', '.join(sorted(allowed))}")
    return value


def _validate_access(value: object, location: str, expected: set[str], errors: list[str]) -> None:
    access = _string_list(value, location, errors)
    if access and set(access) != expected:
        errors.append(f"contract: {location} must contain exactly {', '.join(sorted(expected))}")


def _validate_bluetooth(contract: dict[str, Any], errors: list[str]) -> None:
    bluetooth = _mapping(contract.get("bluetooth"), "bluetooth", errors)
    values: list[str] = []
    for key in ("service_uuid", "data_char_uuid", "config_char_uuid"):
        value = _required_string(bluetooth, key, "bluetooth", errors)
        if value and not UUID_RE.fullmatch(value):
            errors.append(f"contract: bluetooth.{key} must be a lowercase UUID")
        if value:
            values.append(value)
    if len(values) != len(set(values)):
        errors.append("contract: bluetooth UUIDs must be unique")


def _validate_data_fields(fields: object, data_length: int | None, errors: list[str]) -> set[str]:
    if not isinstance(fields, list) or not fields:
        errors.append("contract: frame.data.fields must be a non-empty list")
        return set()
    names: list[str] = []
    spans: list[tuple[int, int]] = []
    for index, field in enumerate(fields):
        if not isinstance(field, dict):
            errors.append(f"contract: frame.data.fields[{index}] must be an object")
            continue
        location = f"frame.data.fields[{index}]"
        name = _required_string(field, "name", location, errors)
        field_type = _required_choice(field, "type", location, set(TYPE_WIDTHS), errors)
        offset = _integer(field.get("offset"), f"{location}.offset", errors)
        if name:
            names.append(name)
        if offset is not None and offset < 0:
            errors.append(f"contract: {location}.offset must not be negative")
        elif offset is not None and field_type in TYPE_WIDTHS:
            spans.append((offset, offset + TYPE_WIDTHS[field_type]))
    if len(names) != len(set(names)):
        errors.append("contract: frame.data field names must be unique")
    if len(spans) == len(fields):
        expected_start = 0
        contiguous = True
        for start, end in spans:
            if start != expected_start:
                contiguous = False
            expected_start = end
        if not contiguous:
            errors.append(
                "contract: frame.data field spans must be ordered, contiguous, and non-overlapping"
            )
        if data_length is not None and expected_start != data_length:
            errors.append("contract: frame.data.byte_length must end at the final field")
    return {f"CH{index}" for index in range(1, len(fields) + 1)}


def _validate_config(frame: dict[str, Any], errors: list[str]) -> None:
    config = _mapping(frame.get("config"), "frame.config", errors)
    config_length = _integer(
        config.get("byte_length"), "frame.config.byte_length", errors, positive=True
    )
    _validate_access(config.get("access"), "frame.config.access", CONFIG_ACCESS, errors)
    _required_choice(config, "encoding", "frame.config", {WIRE_ENCODING}, errors)
    config_type = _required_choice(config, "type", "frame.config", set(TYPE_WIDTHS), errors)
    config_width = TYPE_WIDTHS.get(config_type)
    if config_length is not None and config_width is not None and config_length != config_width:
        errors.append("contract: frame.config.byte_length must match its scalar type")
    selection = _mapping(config.get("selection"), "frame.config.selection", errors)
    _required_choice(selection, "rounding", "frame.config.selection", {"nearest_integer"}, errors)
    minimum = _number(selection.get("minimum"), "frame.config.selection.minimum", errors)
    maximum = _number(
        selection.get("maximum_exclusive"),
        "frame.config.selection.maximum_exclusive",
        errors,
    )
    _required_choice(
        selection,
        "invalid_behavior",
        "frame.config.selection",
        {"keep_active_mode"},
        errors,
    )
    if minimum is not None and maximum is not None and minimum >= maximum:
        errors.append("contract: frame.config selection range must be increasing")


def _validate_frame(contract: dict[str, Any], errors: list[str]) -> set[str]:
    frame = _mapping(contract.get("frame"), "frame", errors)
    _integer(frame.get("sample_period_ms"), "frame.sample_period_ms", errors, positive=True)
    data = _mapping(frame.get("data"), "frame.data", errors)
    data_length = _integer(data.get("byte_length"), "frame.data.byte_length", errors, positive=True)
    _validate_access(data.get("access"), "frame.data.access", DATA_ACCESS, errors)
    _required_choice(data, "encoding", "frame.data", {WIRE_ENCODING}, errors)
    fields = data.get("fields")
    channel_keys = _validate_data_fields(fields, data_length, errors)
    _validate_config(frame, errors)
    return channel_keys


def _validate_mode_record(
    mode: object, index: int, channel_keys: set[str], errors: list[str]
) -> tuple[int | None, str, str]:
    location = f"modes.active[{index}]"
    if not isinstance(mode, dict):
        errors.append(f"contract: {location} must be an object")
        return None, "", ""
    mode_id = _integer(mode.get("id"), f"{location}.id", errors, positive=True)
    name = _required_string(mode, "name", location, errors)
    if name and not MODE_NAME_RE.fullmatch(name):
        errors.append(f"contract: {location}.name must be a lowercase identifier")
    experiment = _required_string(mode, "experiment", location, errors)
    if experiment and (
        not experiment.endswith(".phyphox")
        or "/" in experiment
        or "\\" in experiment
        or experiment in {".phyphox", "..phyphox"}
    ):
        errors.append(f"contract: {location}.experiment must be a .phyphox filename")
    channels = mode.get("channels")
    if not isinstance(channels, dict) or set(channels) != channel_keys:
        errors.append(f"contract: {location}.channels must match frame data fields")
    elif any(not isinstance(value, str) or not value for value in channels.values()):
        errors.append(f"contract: {location}.channels must describe each channel")
    return mode_id, name, experiment


def _reserved_mode_ids(modes: dict[str, Any], errors: list[str]) -> list[int]:
    reserved = modes.get("reserved")
    if not isinstance(reserved, list):
        errors.append("contract: modes.reserved must be a list")
        return []
    reserved_ids = [
        reserved_id
        for index, value in enumerate(reserved)
        if (reserved_id := _integer(value, f"modes.reserved[{index}]", errors, positive=True))
        is not None
    ]
    if len(reserved_ids) != len(set(reserved_ids)):
        errors.append("contract: reserved mode IDs must be unique integers")
    return reserved_ids


def _selection_range(contract: dict[str, Any]) -> tuple[object, object]:
    frame = contract.get("frame", {})
    config = frame.get("config", {}) if isinstance(frame, dict) else {}
    selection = config.get("selection", {}) if isinstance(config, dict) else {}
    if not isinstance(selection, dict):
        return None, None
    return selection.get("minimum"), selection.get("maximum_exclusive")


def _validate_modes(contract: dict[str, Any], channel_keys: set[str], errors: list[str]) -> None:
    modes = _mapping(contract.get("modes"), "modes", errors)
    default = _integer(modes.get("default"), "modes.default", errors, positive=True)
    active = modes.get("active")
    if not isinstance(active, list) or not active:
        errors.append("contract: modes.active must be a non-empty list")
        active = []
    records = [
        _validate_mode_record(mode, index, channel_keys, errors)
        for index, mode in enumerate(active)
    ]
    ids = [mode_id for mode_id, _, _ in records if mode_id is not None]
    names = [name for _, name, _ in records if name]
    experiments = [experiment for _, _, experiment in records if experiment]
    if len(ids) != len(set(ids)):
        errors.append("contract: active mode IDs must be unique integers")
    if len(names) != len(set(names)):
        errors.append("contract: active mode names must be unique")
    if len(set(experiments)) != len(experiments):
        errors.append("contract: active mode experiment filenames must be unique")
    reserved_ids = _reserved_mode_ids(modes, errors)
    if set(ids) & set(reserved_ids):
        errors.append("contract: active and reserved mode IDs must not overlap")
    if default is not None and default not in ids:
        errors.append("contract: modes.default must name an active mode")
    minimum, maximum = _selection_range(contract)
    if (
        isinstance(minimum, (int, float))
        and not isinstance(minimum, bool)
        and isinstance(maximum, (int, float))
        and not isinstance(maximum, bool)
        and any(not minimum <= mode_id < maximum for mode_id in ids)
    ):
        errors.append("contract: active mode IDs must fit the config selection range")


def contract_errors(raw: object) -> list[str]:
    """Return schema errors for a raw contract without mutating it."""

    if not isinstance(raw, dict):
        return ["contract: root must be an object"]
    errors: list[str] = []
    schema_version = raw.get("schema_version")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != 1
    ):
        errors.append("contract: schema_version must be 1")
    device = _mapping(raw.get("device"), "device", errors)
    _required_string(device, "name", "device", errors)
    _validate_bluetooth(raw, errors)
    channel_keys = _validate_frame(raw, errors)
    _validate_modes(raw, channel_keys, errors)
    return errors


def parse_protocol(raw: object) -> Protocol:
    """Build the typed model from a raw contract that has no ``contract_errors``."""

    if not isinstance(raw, dict):
        raise TypeError("contract root must be an object")
    bluetooth = raw["bluetooth"]
    frame = raw["frame"]
    modes = raw["modes"]
    return Protocol(
        device_name=raw["device"]["name"],
        service_uuid=bluetooth["service_uuid"],
        data_char_uuid=bluetooth["data_char_uuid"],
        config_char_uuid=bluetooth["config_char_uuid"],
        sample_period_ms=frame["sample_period_ms"],
        data_encoding=frame["data"]["encoding"],
        data_offsets=tuple(field["offset"] for field in frame["data"]["fields"]),
        config_encoding=frame["config"]["encoding"],
        default_mode=modes["default"],
        modes=tuple(
            Mode(
                id=mode["id"],
                name=mode["name"],
                experiment=mode["experiment"],
                channels=tuple(mode["channels"].items()),
            )
            for mode in modes["active"]
        ),
        reserved_modes=tuple(modes["reserved"]),
    )


def load_protocol(path: Path) -> Protocol:
    """Read, validate, and parse the contract, raising ToolError on any problem."""

    raw = read_contract(path)
    errors = contract_errors(raw)
    if errors:
        raise ToolError("\n".join(errors))
    return parse_protocol(raw)
