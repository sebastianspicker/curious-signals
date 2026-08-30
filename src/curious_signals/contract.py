"""Loading and structural validation for the repository BLE contract."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from .layout import contract_path

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
TYPE_WIDTHS = {"float32": 4}


def load_contract(path: Path | None = None) -> dict[str, Any]:
    """Load the canonical JSON contract, raising ValueError for invalid JSON."""

    target = path or contract_path()
    try:
        content = target.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"{target}: cannot read contract: {error}") from error
    try:
        loaded = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(f"{target}: invalid JSON: {error}") from error
    if not isinstance(loaded, dict):
        raise ValueError(f"{target}: contract root must be an object")
    return loaded


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


def _validate_frame(contract: dict[str, Any], errors: list[str]) -> set[str]:
    frame = _mapping(contract.get("frame"), "frame", errors)
    _integer(frame.get("sample_period_ms"), "frame.sample_period_ms", errors, positive=True)
    data = _mapping(frame.get("data"), "frame.data", errors)
    data_length = _integer(data.get("byte_length"), "frame.data.byte_length", errors, positive=True)
    _string_list(data.get("access"), "frame.data.access", errors)
    _required_string(data, "encoding", "frame.data", errors)
    fields = data.get("fields")
    channel_keys: set[str] = set()
    if not isinstance(fields, list) or not fields:
        errors.append("contract: frame.data.fields must be a non-empty list")
    else:
        names: list[str] = []
        offsets: list[int] = []
        ends: list[int] = []
        for index, field in enumerate(fields):
            if not isinstance(field, dict):
                errors.append(f"contract: frame.data.fields[{index}] must be an object")
                continue
            location = f"frame.data.fields[{index}]"
            name = _required_string(field, "name", location, errors)
            field_type = _required_string(field, "type", location, errors)
            offset = _integer(field.get("offset"), f"{location}.offset", errors)
            width = TYPE_WIDTHS.get(field_type)
            if field_type and width is None:
                errors.append(f"contract: {location}.type is not supported")
            if offset is not None and offset < 0:
                errors.append(f"contract: {location}.offset must not be negative")
            if name:
                names.append(name)
            if offset is not None:
                offsets.append(offset)
                if width is not None:
                    ends.append(offset + width)
        if len(names) != len(set(names)):
            errors.append("contract: frame.data field names must be unique")
        if len(offsets) != len(set(offsets)):
            errors.append("contract: frame.data field offsets must be unique")
        if offsets and offsets != sorted(offsets):
            errors.append("contract: frame.data fields must be ordered by offset")
        if data_length is not None and ends and max(ends) != data_length:
            errors.append("contract: frame.data.byte_length must end at the final field")
        channel_keys = {f"CH{index}" for index in range(1, len(fields) + 1)}
    config = _mapping(frame.get("config"), "frame.config", errors)
    config_length = _integer(
        config.get("byte_length"), "frame.config.byte_length", errors, positive=True
    )
    _string_list(config.get("access"), "frame.config.access", errors)
    _required_string(config, "encoding", "frame.config", errors)
    config_type = _required_string(config, "type", "frame.config", errors)
    config_width = TYPE_WIDTHS.get(config_type)
    if config_type and config_width is None:
        errors.append("contract: frame.config.type is not supported")
    if config_length is not None and config_width is not None and config_length != config_width:
        errors.append("contract: frame.config.byte_length must match its scalar type")
    selection = _mapping(config.get("selection"), "frame.config.selection", errors)
    _required_string(selection, "rounding", "frame.config.selection", errors)
    minimum = _number(selection.get("minimum"), "frame.config.selection.minimum", errors)
    maximum = _number(
        selection.get("maximum_exclusive"),
        "frame.config.selection.maximum_exclusive",
        errors,
    )
    _required_string(selection, "invalid_behavior", "frame.config.selection", errors)
    if minimum is not None and maximum is not None and minimum >= maximum:
        errors.append("contract: frame.config selection range must be increasing")
    return channel_keys


def _validate_modes(contract: dict[str, Any], channel_keys: set[str], errors: list[str]) -> None:
    modes = _mapping(contract.get("modes"), "modes", errors)
    default = _integer(modes.get("default"), "modes.default", errors)
    active = modes.get("active")
    if not isinstance(active, list):
        errors.append("contract: modes.active must be a list")
        active = []
    ids: list[int] = []
    names: list[str] = []
    experiments: list[str] = []
    for index, mode in enumerate(active):
        if not isinstance(mode, dict):
            errors.append(f"contract: modes.active[{index}] must be an object")
            continue
        mode_id = _integer(mode.get("id"), f"modes.active[{index}].id", errors)
        if mode_id is not None:
            ids.append(mode_id)
        name = _required_string(mode, "name", f"modes.active[{index}]", errors)
        if name:
            names.append(name)
        experiment = _required_string(mode, "experiment", f"modes.active[{index}]", errors)
        if experiment:
            experiments.append(experiment)
            if not experiment.endswith(".phyphox"):
                errors.append(f"contract: modes.active[{index}].experiment must end in .phyphox")
        channels = mode.get("channels")
        if not isinstance(channels, dict) or set(channels) != channel_keys:
            errors.append(f"contract: modes.active[{index}].channels must match frame data fields")
        elif any(not isinstance(value, str) or not value for value in channels.values()):
            errors.append(f"contract: modes.active[{index}].channels must describe each channel")
    if len(ids) != len(set(ids)):
        errors.append("contract: active mode IDs must be unique integers")
    if len(names) != len(set(names)):
        errors.append("contract: active mode names must be unique")
    if len(set(experiments)) != len(experiments):
        errors.append("contract: active mode experiment filenames must be unique")
    reserved = modes.get("reserved")
    reserved_ids: list[int] = []
    if not isinstance(reserved, list):
        errors.append("contract: modes.reserved must be a list")
    else:
        for index, value in enumerate(reserved):
            reserved_id = _integer(value, f"modes.reserved[{index}]", errors)
            if reserved_id is not None:
                reserved_ids.append(reserved_id)
        if len(reserved_ids) != len(set(reserved_ids)):
            errors.append("contract: reserved mode IDs must be unique integers")
    if set(ids) & set(reserved_ids):
        errors.append("contract: active and reserved mode IDs must not overlap")
    if default is not None and default not in ids:
        errors.append("contract: modes.default must name an active mode")


def validate_contract(contract: dict[str, Any] | None = None) -> list[str]:
    """Return schema errors without mutating the supplied contract."""

    errors: list[str] = []
    if contract is None:
        try:
            contract = load_contract()
        except ValueError as error:
            return [str(error)]
    if not isinstance(contract, dict):
        return ["contract: root must be an object"]
    if contract.get("schema_version") != 1:
        errors.append("contract: schema_version must be 1")
    device = _mapping(contract.get("device"), "device", errors)
    _required_string(device, "name", "device", errors)
    _validate_bluetooth(contract, errors)
    channel_keys = _validate_frame(contract, errors)
    _validate_modes(contract, channel_keys, errors)
    return errors


def active_modes(contract: dict[str, Any]) -> list[dict[str, Any]]:
    """Return active mode records after callers have validated the contract."""

    modes = contract.get("modes", {})
    active = modes.get("active", []) if isinstance(modes, dict) else []
    return [mode for mode in active if isinstance(mode, dict)]
