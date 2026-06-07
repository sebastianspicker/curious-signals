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
    (
        r"^constexpr const char\*\s+"
        r'(kPhyphoxServiceUuid|kDataCharUuid|kConfigCharUuid)\s*=\s*"([^"]+)";'
    )
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
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _child(parent: ET.Element, name: str) -> ET.Element | None:
    for c in list(parent):
        if _local_name(c.tag) == name:
            return c
    return None


def _children(parent: ET.Element, name: str) -> list[ET.Element]:
    out: list[ET.Element] = []
    for c in list(parent):
        if _local_name(c.tag) == name:
            out.append(c)
    return out


def _text(e: ET.Element | None) -> str | None:
    if e is None or e.text is None:
        return None
    t = e.text.strip()
    return t if t else None


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
    errors: list[ValidationError] = []
    try:
        constants = json.loads(constants_path.read_text(encoding="utf-8"))
    except OSError as e:
        return None, None, None, [ValidationError(f"{constants_path}: cannot read file: {e}")]
    except json.JSONDecodeError as e:
        return None, None, None, [ValidationError(f"{constants_path}: invalid JSON: {e}")]

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
    service_uuid: str | None = None
    data_uuid: str | None = None
    config_uuid: str | None = None
    errors: list[ValidationError] = []
    try:
        for line in sketch_path.read_text(encoding="utf-8").splitlines():
            match = SKETCH_UUID_RE.match(line.strip())
            if not match:
                continue
            key, value = match.groups()
            if key == "kPhyphoxServiceUuid":
                service_uuid = value
            elif key == "kDataCharUuid":
                data_uuid = value
            elif key == "kConfigCharUuid":
                config_uuid = value
    except OSError as e:
        return None, None, None, [ValidationError(f"{sketch_path}: cannot read file: {e}")]

    if not service_uuid:
        errors.append(ValidationError(f"{sketch_path}: missing required kPhyphoxServiceUuid"))
    if not data_uuid:
        errors.append(ValidationError(f"{sketch_path}: missing required kDataCharUuid"))
    if not config_uuid:
        errors.append(ValidationError(f"{sketch_path}: missing required kConfigCharUuid"))
    return service_uuid, data_uuid, config_uuid, errors


def _uuid_mismatch_errors(
    constants_path: Path,
    sketch_path: Path,
    constants_uuids: tuple[str | None, str | None, str | None],
    sketch_uuids: tuple[str | None, str | None, str | None],
) -> list[ValidationError]:
    constants_service_uuid, constants_data_uuid, constants_config_uuid = constants_uuids
    sketch_service_uuid, sketch_data_uuid, sketch_config_uuid = sketch_uuids
    errors: list[ValidationError] = []
    if (
        constants_service_uuid
        and sketch_service_uuid
        and constants_service_uuid != sketch_service_uuid
    ):
        errors.append(
            ValidationError(f"{constants_path}: service_uuid does not match {sketch_path}")
        )

    if constants_data_uuid and sketch_data_uuid and constants_data_uuid != sketch_data_uuid:
        errors.append(
            ValidationError(f"{constants_path}: data_char_uuid does not match {sketch_path}")
        )
    if constants_config_uuid and sketch_config_uuid and constants_config_uuid != sketch_config_uuid:
        errors.append(
            ValidationError(f"{constants_path}: config_char_uuid does not match {sketch_path}")
        )
    return errors


def _load_expected_uuids() -> tuple[str | None, str | None, str | None, list[ValidationError]]:
    constants_path = REPO_ROOT / "experiments" / "phyphox_constants.json"
    sketch_path = REPO_ROOT / "arduino" / "phyphox_ble_sense" / "phyphox_ble_sense.ino"
    constants_uuids = _read_constants_uuids(constants_path)
    sketch_uuids = _read_sketch_uuids(sketch_path)
    errors = [*constants_uuids[3], *sketch_uuids[3]]
    errors.extend(
        _uuid_mismatch_errors(
            constants_path,
            sketch_path,
            constants_uuids[:3],
            sketch_uuids[:3],
        )
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
    except OSError as e:
        return constants_modes, [ValidationError(f"{constants_path}: cannot read file: {e}")], False
    except json.JSONDecodeError as e:
        return constants_modes, [ValidationError(f"{constants_path}: invalid JSON: {e}")], False

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


def _load_sketch_modes(sketch_path: Path) -> tuple[dict[str, int], list[ValidationError], bool]:
    errors: list[ValidationError] = []
    sketch_modes: dict[str, int] = {}
    try:
        in_enum = False
        for line in sketch_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("enum class Mode"):
                in_enum = True
                continue
            if in_enum and stripped == "};":
                break
            if not in_enum:
                continue
            match = MODE_ID_RE.match(stripped)
            if not match:
                continue
            raw_name, value = match.groups()
            mapped_name = MODE_NAME_MAP.get(raw_name)
            if mapped_name:
                sketch_modes[mapped_name] = int(value)
    except OSError as e:
        return sketch_modes, [ValidationError(f"{sketch_path}: cannot read file: {e}")], False

    for name in MODE_NAME_MAP.values():
        if name not in sketch_modes:
            errors.append(ValidationError(f"{sketch_path}: missing required mode {name}"))
    return sketch_modes, errors, True


def _load_source_mode_ids(
    source_dir: Path, constants_modes: dict[str, int]
) -> tuple[set[int], list[ValidationError]]:
    errors: list[ValidationError] = []
    source_mode_ids: set[int] = set()
    for path in sorted(source_dir.glob("*.phyphox.xml")):
        try:
            root = ET.parse(path).getroot()
        except (OSError, ET.ParseError) as e:
            errors.append(ValidationError(f"{path}: cannot parse mode config: {e}"))
            continue
        config = root.find("./output/bluetooth/config")
        if config is None or config.text is None:
            errors.append(ValidationError(f"{path}: missing output bluetooth config value"))
            continue
        raw_config = config.text.strip()
        try:
            numeric_config = float(raw_config)
        except ValueError:
            errors.append(ValidationError(f"{path}: invalid output bluetooth config value"))
            continue
        if (
            not math.isfinite(numeric_config)
            or not numeric_config.is_integer()
            or int(numeric_config) not in set(constants_modes.values())
        ):
            errors.append(
                ValidationError(
                    f"{path}: output bluetooth config value must be an active integer mode ID"
                )
            )
            continue
        source_mode_ids.add(int(numeric_config))
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


def _validate_root_contract(path: str, root: ET.Element) -> tuple[list[ValidationError], bool]:
    errors: list[ValidationError] = []
    if _local_name(root.tag) != "phyphox":
        errors.append(
            ValidationError(
                f"{path}: root element must be <phyphox> (got <{_local_name(root.tag)}>)"
            )
        )
        return errors, False

    if not root.attrib.get("version"):
        errors.append(ValidationError(f"{path}: <phyphox> missing required attribute version"))

    required_top = ["title", "category", "description", "data-containers", "input", "views"]
    for name in required_top:
        if _child(root, name) is None:
            errors.append(ValidationError(f"{path}: missing required top-level <{name}> element"))
    return errors, True


def _container_names(path: str, root: ET.Element) -> tuple[list[str], list[ValidationError]]:
    errors: list[ValidationError] = []
    names: list[str] = []
    containers_el = _child(root, "data-containers")
    if containers_el is None:
        return names, errors

    for container in _children(containers_el, "container"):
        name = _text(container)
        if not name:
            errors.append(
                ValidationError(f"{path}: <data-containers><container> must have non-empty text")
            )
            continue
        names.append(name)
    return names, errors


def _duplicate_container_errors(path: str, container_names: list[str]) -> list[ValidationError]:
    if len(set(container_names)) == len(container_names):
        return []

    seen: set[str] = set()
    duplicates: set[str] = set()
    for name in container_names:
        if name in seen:
            duplicates.add(name)
        seen.add(name)
    return [
        ValidationError(
            f"{path}: duplicate <container> names: {', '.join(sorted(duplicates))}"
        )
    ]


def _input_references(root: ET.Element) -> set[str]:
    referenced: set[str] = set()
    input_el = _child(root, "input")
    if input_el is not None:
        for bt in _children(input_el, "bluetooth"):
            for out in _children(bt, "output"):
                if target := _text(out):
                    referenced.add(target)
    return referenced


def _section_references(root: ET.Element, parent_name: str, allowed_tags: set[str]) -> set[str]:
    parent = _child(root, parent_name)
    if parent is None:
        return set()

    referenced: set[str] = set()
    for element in parent.iter():
        if _local_name(element.tag) not in allowed_tags:
            continue
        if target := _text(element):
            referenced.add(target)
    return referenced


def _referenced_container_names(root: ET.Element) -> set[str]:
    referenced = _input_references(root)
    referenced.update(_section_references(root, "views", {"input"}))
    referenced.update(_section_references(root, "analysis", {"input", "output"}))
    referenced.update(_section_references(root, "export", {"data"}))
    return referenced


def _record_bluetooth_output(
    path: str, output: ET.Element, state: BluetoothInputState
) -> list[ValidationError]:
    if output.attrib.get("extra") == "time":
        state.has_extra_time = True
        return []

    errors: list[ValidationError] = []
    target_name = _text(output)
    if char := output.attrib.get("char"):
        state.data_chars.add(char)

    offset = output.attrib.get("offset")
    if offset is None:
        missing_name = target_name or "<unnamed>"
        errors.append(
            ValidationError(f"{path}: missing required bluetooth output offset for {missing_name}")
        )
        return errors

    try:
        state.offsets.append(int(offset))
    except ValueError:
        errors.append(ValidationError(f"{path}: invalid bluetooth output offset: {offset!r}"))
    return errors


def _unknown_reference_errors(
    path: str, referenced: set[str], container_names: list[str]
) -> list[ValidationError]:
    unknown = sorted(name for name in referenced if name not in set(container_names))
    if not unknown:
        return []
    return [ValidationError(f"{path}: references unknown data containers: {', '.join(unknown)}")]


def _validate_bluetooth_input_outputs(
    path: str, outputs: list[ET.Element], expected_data_uuid: str | None
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    state = BluetoothInputState(data_chars=set(), offsets=[])
    for output in outputs:
        errors.extend(_record_bluetooth_output(path, output, state))

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

    duplicate_offsets = sorted(
        offset for offset in set(state.offsets) if state.offsets.count(offset) > 1
    )
    if duplicate_offsets:
        errors.append(
            ValidationError(f"{path}: duplicate bluetooth output offsets: {duplicate_offsets}")
        )
    if state.offsets and set(state.offsets) != EXPECTED_OFFSETS:
        errors.append(
            ValidationError(
                f"{path}: expected float32 offsets {sorted(EXPECTED_OFFSETS)} "
                f"(got {sorted(set(state.offsets))})"
            )
        )
    return errors


def _validate_config_element(
    path: str, config: ET.Element, expected_config_uuid: str | None
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    if config.attrib.get("conversion") != "float32LittleEndian":
        errors.append(
            ValidationError(
                f"{path}: expected config conversion float32LittleEndian "
                f"(got {config.attrib.get('conversion')!r})"
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
    path: str, root: ET.Element, input_bt_id: str | None, expected_config_uuid: str | None
) -> list[ValidationError]:
    out_el = _child(root, "output")
    if out_el is None:
        return [ValidationError(f"{path}: missing <output> (used to push config to device)")]

    bt_outs = _children(out_el, "bluetooth")
    if len(bt_outs) != 1:
        return [
            ValidationError(
                f"{path}: expected exactly one <output><bluetooth> block (found {len(bt_outs)})"
            )
        ]

    errors: list[ValidationError] = []
    bt_out = bt_outs[0]
    if input_bt_id and bt_out.attrib.get("id") != input_bt_id:
        errors.append(
            ValidationError(f"{path}: bluetooth id mismatch between <input> and <output>")
        )

    configs = _children(bt_out, "config")
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
    path: str,
    root: ET.Element,
    expected_data_uuid: str | None,
    expected_config_uuid: str | None,
) -> list[ValidationError]:
    input_el = _child(root, "input")
    if input_el is None:
        return []

    bt_inputs = _children(input_el, "bluetooth")
    if len(bt_inputs) != 1:
        return [
            ValidationError(
                f"{path}: expected exactly one <input><bluetooth> block (found {len(bt_inputs)})"
            )
        ]

    errors: list[ValidationError] = []
    bt = bt_inputs[0]
    bt_id = bt.attrib.get("id")
    if not bt_id:
        errors.append(ValidationError(f"{path}: <input><bluetooth> missing required attribute id"))

    outputs = _children(bt, "output")
    if len(outputs) < 2:
        errors.append(ValidationError(f"{path}: <input><bluetooth> must contain <output> mappings"))
    else:
        errors.extend(_validate_bluetooth_input_outputs(path, outputs, expected_data_uuid))
    errors.extend(_validate_bluetooth_config_output(path, root, bt_id, expected_config_uuid))
    return errors


def validate_phyphox(
    path: str, expected_data_uuid: str | None = None, expected_config_uuid: str | None = None
) -> list[ValidationError]:
    errors: list[ValidationError] = []

    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except OSError as e:
        return [ValidationError(f"{path}: cannot read file: {e}")]
    except ET.ParseError as e:
        return [ValidationError(f"{path}: XML parse error: {e}")]

    root_errors, should_continue = _validate_root_contract(path, root)
    errors.extend(root_errors)
    if not should_continue:
        return errors

    container_names, container_errors = _container_names(path, root)
    errors.extend(container_errors)
    errors.extend(_duplicate_container_errors(path, container_names))
    errors.extend(
        _unknown_reference_errors(path, _referenced_container_names(root), container_names)
    )
    errors.extend(
        _validate_bluetooth_contract(path, root, expected_data_uuid, expected_config_uuid)
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
        for e in errors:
            print(e.message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
