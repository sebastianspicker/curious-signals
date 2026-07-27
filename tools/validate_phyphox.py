#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_OFFSETS = {0, 4, 8, 12, 16}
SKETCH_UUID_RE = re.compile(
    r"^constexpr const char\*\s+"
    r'(kPhyphoxServiceUuid|kDataCharUuid|kConfigCharUuid)\s*=\s*"([^"]+)";'
)
MODE_ID_RE = re.compile(r"^\s*k([A-Za-z0-9]+)\s*=\s*(\d+),?$")
MODE_NAME_MAP = {
    "Acceleration": "acceleration",
    "Gyroscope": "gyroscope",
    "Magnetometer": "magnetometer",
    "Pressure": "pressure",
    "TemperatureHumidity": "temperature_humidity",
    "LightRgb": "light_rgb",
    "AnalogInputs": "analog_inputs",
}


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def _child(parent: ET.Element, name: str) -> ET.Element | None:
    return next((child for child in parent if _local_name(child.tag) == name), None)


def _children(parent: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in parent if _local_name(child.tag) == name]


def _text(element: ET.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    text = element.text.strip()
    return text or None


@dataclass(frozen=True)
class ValidationError:
    message: str


@dataclass
class BluetoothInputState:
    data_chars: set[str]
    offsets: list[int]
    has_extra_time: bool = False


def _read_constants_uuids(
    constants_path: Path,
) -> tuple[str | None, str | None, str | None, list[ValidationError]]:
    try:
        constants = json.loads(constants_path.read_text(encoding="utf-8"))
    except OSError as error:
        return None, None, None, [ValidationError(f"{constants_path}: cannot read file: {error}")]
    except json.JSONDecodeError as error:
        return None, None, None, [ValidationError(f"{constants_path}: invalid JSON: {error}")]

    bluetooth = constants.get("bluetooth", {})
    errors = [
        ValidationError(f"{constants_path}: missing required bluetooth.{key}")
        for key in ("service_uuid", "data_char_uuid", "config_char_uuid")
        if not bluetooth.get(key)
    ]
    return (
        bluetooth.get("service_uuid"),
        bluetooth.get("data_char_uuid"),
        bluetooth.get("config_char_uuid"),
        errors,
    )


def _read_sketch_uuids(
    sketch_path: Path,
) -> tuple[str | None, str | None, str | None, list[ValidationError]]:
    values: dict[str, str] = {}
    errors: list[ValidationError] = []
    try:
        for line in sketch_path.read_text(encoding="utf-8").splitlines():
            match = SKETCH_UUID_RE.match(line.strip())
            if match:
                values[match.group(1)] = match.group(2)
    except OSError as error:
        errors.append(ValidationError(f"{sketch_path}: cannot read file: {error}"))

    keys = ("kPhyphoxServiceUuid", "kDataCharUuid", "kConfigCharUuid")
    errors.extend(
        ValidationError(f"{sketch_path}: missing required {key}")
        for key in keys
        if not values.get(key)
    )
    return *(values.get(key) for key in keys), errors


def _uuid_mismatch_errors(
    constants_path: Path,
    sketch_path: Path,
    constants_uuids: tuple[str | None, str | None, str | None],
    sketch_uuids: tuple[str | None, str | None, str | None],
) -> list[ValidationError]:
    labels = ("service_uuid", "data_char_uuid", "config_char_uuid")
    return [
        ValidationError(f"{constants_path}: {label} does not match {sketch_path}")
        for label, constant, sketch in zip(labels, constants_uuids, sketch_uuids)
        if constant and sketch and constant != sketch
    ]


def _load_expected_uuids() -> tuple[str | None, str | None, str | None, list[ValidationError]]:
    constants_path = REPO_ROOT / "experiments" / "phyphox_constants.json"
    sketch_path = REPO_ROOT / "arduino" / "phyphox_ble_sense" / "phyphox_ble_sense.ino"
    constants = _read_constants_uuids(constants_path)
    sketch = _read_sketch_uuids(sketch_path)
    errors = [*constants[3], *sketch[3]]
    errors.extend(_uuid_mismatch_errors(constants_path, sketch_path, constants[:3], sketch[:3]))
    return *(constant or source for constant, source in zip(constants[:3], sketch[:3])), errors


def _load_constants_modes(
    constants_path: Path,
) -> tuple[dict[str, int], list[ValidationError], bool]:
    try:
        constants = json.loads(constants_path.read_text(encoding="utf-8"))
    except OSError as error:
        return {}, [ValidationError(f"{constants_path}: cannot read file: {error}")], False
    except json.JSONDecodeError as error:
        return {}, [ValidationError(f"{constants_path}: invalid JSON: {error}")], False

    raw_modes = constants.get("modes", {})
    errors = (
        [] if raw_modes else [ValidationError(f"{constants_path}: missing required modes object")]
    )
    modes = {
        name: value
        for name in MODE_NAME_MAP.values()
        if isinstance(value := raw_modes.get(name), int)
    }
    errors.extend(
        ValidationError(f"{constants_path}: missing required modes.{name}")
        for name in MODE_NAME_MAP.values()
        if name not in modes
    )
    return modes, errors, True


def _iter_mode_enum_lines(lines: list[str]):
    in_enum = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("enum class Mode"):
            in_enum = True
        elif in_enum and stripped == "};":
            return
        elif in_enum:
            yield stripped


def _load_sketch_modes(sketch_path: Path) -> tuple[dict[str, int], list[ValidationError], bool]:
    try:
        lines = sketch_path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return {}, [ValidationError(f"{sketch_path}: cannot read file: {error}")], False

    modes: dict[str, int] = {}
    for line in _iter_mode_enum_lines(lines):
        if match := MODE_ID_RE.match(line):
            raw_name, value = match.groups()
            if name := MODE_NAME_MAP.get(raw_name):
                modes[name] = int(value)
    errors = [
        ValidationError(f"{sketch_path}: missing required mode {name}")
        for name in MODE_NAME_MAP.values()
        if name not in modes
    ]
    return modes, errors, True


def _read_source_mode_value(path: Path) -> tuple[str | None, list[ValidationError]]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as error:
        return None, [ValidationError(f"{path}: cannot parse mode config: {error}")]
    config = root.find("./output/bluetooth/config")
    if config is None or config.text is None:
        return None, [ValidationError(f"{path}: missing output bluetooth config value")]
    return config.text.strip(), []


def _source_mode_id(
    path: Path, raw_value: str, active_mode_ids: set[int]
) -> tuple[int | None, list[ValidationError]]:
    try:
        value = float(raw_value)
    except ValueError:
        return None, [ValidationError(f"{path}: invalid output bluetooth config value")]
    if not math.isfinite(value) or not value.is_integer() or int(value) not in active_mode_ids:
        return None, [
            ValidationError(
                f"{path}: output bluetooth config value must be an active integer mode ID"
            )
        ]
    return int(value), []


def _load_source_mode_ids(
    source_dir: Path, constants_modes: dict[str, int]
) -> tuple[set[int], list[ValidationError]]:
    errors: list[ValidationError] = []
    mode_ids: set[int] = set()
    active_mode_ids = set(constants_modes.values())
    for path in sorted(source_dir.glob("*.phyphox.xml")):
        raw_value, read_errors = _read_source_mode_value(path)
        errors.extend(read_errors)
        if raw_value is None:
            continue
        mode_id, mode_errors = _source_mode_id(path, raw_value, active_mode_ids)
        errors.extend(mode_errors)
        if mode_id is not None:
            mode_ids.add(mode_id)
    return mode_ids, errors


def _load_expected_modes() -> list[ValidationError]:
    constants_path = REPO_ROOT / "experiments" / "phyphox_constants.json"
    sketch_path = REPO_ROOT / "arduino" / "phyphox_ble_sense" / "phyphox_ble_sense.ino"
    source_dir = REPO_ROOT / "src" / "phyphox"
    constants_modes, errors, constants_loaded = _load_constants_modes(constants_path)
    if not constants_loaded:
        return errors
    sketch_modes, sketch_errors, sketch_loaded = _load_sketch_modes(sketch_path)
    errors.extend(sketch_errors)
    if not sketch_loaded:
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


def _validate_root_contract(path: str, root: ET.Element) -> tuple[list[ValidationError], bool]:
    if _local_name(root.tag) != "phyphox":
        return [
            ValidationError(
                f"{path}: root element must be <phyphox> (got <{_local_name(root.tag)}>)"
            )
        ], False
    errors = (
        []
        if root.attrib.get("version")
        else [ValidationError(f"{path}: <phyphox> missing required attribute version")]
    )
    errors.extend(
        ValidationError(f"{path}: missing required top-level <{name}> element")
        for name in ("title", "category", "description", "data-containers", "input", "views")
        if _child(root, name) is None
    )
    return errors, True


def _container_names(path: str, root: ET.Element) -> tuple[list[str], list[ValidationError]]:
    containers = _child(root, "data-containers")
    if containers is None:
        return [], []
    names = [_text(container) for container in _children(containers, "container")]
    errors = [
        ValidationError(f"{path}: <data-containers><container> must have non-empty text")
        for name in names
        if not name
    ]
    return [name for name in names if name], errors


def _duplicate_container_errors(path: str, container_names: list[str]) -> list[ValidationError]:
    duplicates = sorted({name for name in container_names if container_names.count(name) > 1})
    return (
        [ValidationError(f"{path}: duplicate <container> names: {', '.join(duplicates)}")]
        if duplicates
        else []
    )


def _section_references(root: ET.Element, parent_name: str, allowed_tags: set[str]) -> set[str]:
    parent = _child(root, parent_name)
    if parent is None:
        return set()
    return {
        _text(element)
        for element in parent.iter()
        if _local_name(element.tag) in allowed_tags and _text(element)
    }


def _referenced_container_names(root: ET.Element) -> set[str]:
    references = _section_references(root, "views", {"input"})
    references.update(_section_references(root, "analysis", {"input", "output"}))
    references.update(_section_references(root, "export", {"data"}))
    input_element = _child(root, "input")
    if input_element is not None:
        for bluetooth in _children(input_element, "bluetooth"):
            references.update(filter(None, map(_text, _children(bluetooth, "output"))))
    return references


def _unknown_reference_errors(
    path: str, references: set[str], containers: list[str]
) -> list[ValidationError]:
    unknown = sorted(references - set(containers))
    return (
        [ValidationError(f"{path}: references unknown data containers: {', '.join(unknown)}")]
        if unknown
        else []
    )


def _record_bluetooth_output(
    path: str, output: ET.Element, state: BluetoothInputState
) -> list[ValidationError]:
    if output.attrib.get("extra") == "time":
        state.has_extra_time = True
        return []
    if char := output.attrib.get("char"):
        state.data_chars.add(char)
    offset = output.attrib.get("offset")
    if offset is None:
        target_name = _text(output) or "<unnamed>"
        return [
            ValidationError(f"{path}: missing required bluetooth output offset for {target_name}")
        ]
    try:
        state.offsets.append(int(offset))
    except ValueError:
        return [ValidationError(f"{path}: invalid bluetooth output offset: {offset!r}")]
    return []


def _input_mapping_errors(
    path: str, state: BluetoothInputState, expected_data_uuid: str | None
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    if not state.has_extra_time:
        errors.append(ValidationError(f'{path}: missing bluetooth <output extra="time"> mapping'))
    if len(state.data_chars) != 1:
        errors.append(
            ValidationError(f"{path}: expected exactly one data characteristic UUID in inputs")
        )
    if expected_data_uuid and state.data_chars and state.data_chars != {expected_data_uuid}:
        errors.append(
            ValidationError(f"{path}: bluetooth input char UUID must be {expected_data_uuid}")
        )
    return errors


def _offset_errors(path: str, offsets: list[int]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    duplicates = sorted({offset for offset in offsets if offsets.count(offset) > 1})
    if duplicates:
        errors.append(ValidationError(f"{path}: duplicate bluetooth output offsets: {duplicates}"))
    if offsets and set(offsets) != EXPECTED_OFFSETS:
        errors.append(
            ValidationError(
                f"{path}: expected float32 offsets {sorted(EXPECTED_OFFSETS)} "
                f"(got {sorted(set(offsets))})"
            )
        )
    return errors


def _validate_bluetooth_input_outputs(
    path: str, outputs: list[ET.Element], expected_data_uuid: str | None
) -> list[ValidationError]:
    state = BluetoothInputState(data_chars=set(), offsets=[])
    errors = [
        error for output in outputs for error in _record_bluetooth_output(path, output, state)
    ]
    errors.extend(_input_mapping_errors(path, state, expected_data_uuid))
    errors.extend(_offset_errors(path, state.offsets))
    return errors


def _validate_config_element(
    path: str, config: ET.Element, expected_config_uuid: str | None
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    conversion = config.attrib.get("conversion")
    if conversion != "float32LittleEndian":
        errors.append(
            ValidationError(
                f"{path}: expected config conversion float32LittleEndian (got {conversion!r})"
            )
        )
    config_char = config.attrib.get("char")
    if not config_char:
        errors.append(ValidationError(f"{path}: <config> missing required attribute char"))
    elif expected_config_uuid and config_char != expected_config_uuid:
        errors.append(ValidationError(f"{path}: config char UUID must be {expected_config_uuid}"))
    value = _text(config)
    if value is None:
        errors.append(ValidationError(f"{path}: <config> must have a numeric value"))
    else:
        try:
            float(value)
        except ValueError:
            errors.append(ValidationError(f"{path}: <config> value is not numeric: {value!r}"))
    return errors


def _validate_bluetooth_config_output(
    path: str, root: ET.Element, input_id: str | None, expected_config_uuid: str | None
) -> list[ValidationError]:
    output = _child(root, "output")
    if output is None:
        return [ValidationError(f"{path}: missing <output> (used to push config to device)")]
    bluetooth = _children(output, "bluetooth")
    if len(bluetooth) != 1:
        return [
            ValidationError(
                f"{path}: expected exactly one <output><bluetooth> block (found {len(bluetooth)})"
            )
        ]
    errors = []
    if input_id and bluetooth[0].attrib.get("id") != input_id:
        errors.append(
            ValidationError(f"{path}: bluetooth id mismatch between <input> and <output>")
        )
    configs = _children(bluetooth[0], "config")
    if len(configs) != 1:
        errors.append(
            ValidationError(
                f"{path}: expected exactly one <output><bluetooth><config> (found {len(configs)})"
            )
        )
    else:
        errors.extend(_validate_config_element(path, configs[0], expected_config_uuid))
    return errors


def _validate_bluetooth_contract(
    path: str, root: ET.Element, expected_data_uuid: str | None, expected_config_uuid: str | None
) -> list[ValidationError]:
    input_element = _child(root, "input")
    if input_element is None:
        return []
    bluetooth = _children(input_element, "bluetooth")
    if len(bluetooth) != 1:
        return [
            ValidationError(
                f"{path}: expected exactly one <input><bluetooth> block (found {len(bluetooth)})"
            )
        ]
    input_id = bluetooth[0].attrib.get("id")
    errors = (
        []
        if input_id
        else [ValidationError(f"{path}: <input><bluetooth> missing required attribute id")]
    )
    outputs = _children(bluetooth[0], "output")
    if len(outputs) < 2:
        errors.append(ValidationError(f"{path}: <input><bluetooth> must contain <output> mappings"))
    else:
        errors.extend(_validate_bluetooth_input_outputs(path, outputs, expected_data_uuid))
    errors.extend(_validate_bluetooth_config_output(path, root, input_id, expected_config_uuid))
    return errors


def validate_phyphox(
    path: str, expected_data_uuid: str | None = None, expected_config_uuid: str | None = None
) -> list[ValidationError]:
    try:
        root = ET.parse(path).getroot()
    except OSError as error:
        return [ValidationError(f"{path}: cannot read file: {error}")]
    except ET.ParseError as error:
        return [ValidationError(f"{path}: XML parse error: {error}")]
    errors, valid_root = _validate_root_contract(path, root)
    if not valid_root:
        return errors
    containers, container_errors = _container_names(path, root)
    errors.extend(container_errors)
    errors.extend(_duplicate_container_errors(path, containers))
    errors.extend(_unknown_reference_errors(path, _referenced_container_names(root), containers))
    errors.extend(
        _validate_bluetooth_contract(path, root, expected_data_uuid, expected_config_uuid)
    )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plausibility checks for phyphox experiment XML.")
    parser.add_argument("paths", nargs="+", help="Path(s) to *.phyphox file(s)")
    args = parser.parse_args(argv)
    _, expected_data_uuid, expected_config_uuid, errors = _load_expected_uuids()
    errors.extend(_load_expected_modes())
    for path in args.paths:
        errors.extend(validate_phyphox(path, expected_data_uuid, expected_config_uuid))
    for error in errors:
        print(error.message, file=sys.stderr)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
