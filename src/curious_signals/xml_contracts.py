"""Defused XML plausibility checks for generated core phyphox experiments."""

from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException


@dataclass(frozen=True)
class ValidationError:
    message: str


def contract_expectations(
    contract: dict[str, Any], path: str | Path | None = None
) -> dict[str, object]:
    """Return explicit XML validator expectations from one loaded contract."""

    bluetooth = contract["bluetooth"]
    frame = contract["frame"]
    fields = frame["data"]["fields"]
    active = contract["modes"]["active"]
    filename = Path(path).name.removesuffix(".xml") if path is not None else None
    mode_by_file = {mode["experiment"]: mode["id"] for mode in active}
    return {
        "expected_data_uuid": bluetooth["data_char_uuid"],
        "expected_config_uuid": bluetooth["config_char_uuid"],
        "expected_offsets": {field["offset"] for field in fields},
        "expected_data_conversion": frame["data"]["encoding"],
        "expected_config_conversion": frame["config"]["encoding"],
        "expected_mapping": {
            field["offset"]: f"CH{index}" for index, field in enumerate(fields, start=1)
        },
        "expected_mode": mode_by_file.get(filename),
        "valid_modes": {mode["id"] for mode in active},
    }


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _children(parent: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in parent if _local_name(child.tag) == name]


def _child(parent: ET.Element, name: str) -> ET.Element | None:
    children = _children(parent, name)
    return children[0] if children else None


def _text(element: ET.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    return element.text.strip() or None


def _root_errors(path: str, root: ET.Element) -> tuple[list[ValidationError], bool]:
    if _local_name(root.tag) != "phyphox":
        message = f"{path}: root element must be <phyphox> (got <{_local_name(root.tag)}>)"
        return [ValidationError(message)], False
    errors: list[ValidationError] = []
    if not root.attrib.get("version"):
        errors.append(ValidationError(f"{path}: <phyphox> missing required attribute version"))
    for name in ("title", "category", "description", "data-containers", "input", "views"):
        if _child(root, name) is None:
            errors.append(ValidationError(f"{path}: missing required top-level <{name}> element"))
    return errors, True


def _container_errors(path: str, root: ET.Element) -> tuple[list[str], list[ValidationError]]:
    containers = _child(root, "data-containers")
    if containers is None:
        return [], []
    names: list[str] = []
    errors: list[ValidationError] = []
    for container in _children(containers, "container"):
        name = _text(container)
        if name is None:
            errors.append(
                ValidationError(f"{path}: <data-containers><container> must have non-empty text")
            )
        else:
            names.append(name)
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        errors.append(
            ValidationError(f"{path}: duplicate <container> names: {', '.join(duplicates)}")
        )
    return names, errors


def _references(root: ET.Element) -> Iterator[str]:
    input_element = _child(root, "input")
    if input_element is not None:
        for bluetooth in _children(input_element, "bluetooth"):
            for output in _children(bluetooth, "output"):
                if target := _text(output):
                    yield target
    sections = (
        ("views", {"input"}),
        ("analysis", {"input", "output"}),
        ("export", {"data"}),
    )
    for parent_name, tags in sections:
        parent = _child(root, parent_name)
        if parent is not None:
            for element in parent.iter():
                if _local_name(element.tag) in tags and (target := _text(element)):
                    yield target


def _bluetooth_errors(
    path: str,
    root: ET.Element,
    expected_data_uuid: str | None,
    expected_config_uuid: str | None,
    expected_offsets: set[int] | None,
    expected_data_conversion: str | None,
    expected_config_conversion: str | None,
    expected_mapping: dict[int, str] | None,
    expected_mode: int | None,
    valid_modes: set[int] | None,
) -> list[ValidationError]:
    input_element = _child(root, "input")
    if input_element is None:
        return []
    bluetooth_inputs = _children(input_element, "bluetooth")
    if len(bluetooth_inputs) != 1:
        return [
            ValidationError(
                f"{path}: expected exactly one <input><bluetooth> block "
                f"(found {len(bluetooth_inputs)})"
            )
        ]
    bluetooth = bluetooth_inputs[0]
    bluetooth_id = bluetooth.attrib.get("id")
    errors: list[ValidationError] = []
    if not bluetooth_id:
        errors.append(ValidationError(f"{path}: <input><bluetooth> missing required attribute id"))
    outputs = _children(bluetooth, "output")
    if len(outputs) < 2:
        errors.append(ValidationError(f"{path}: <input><bluetooth> must contain <output> mappings"))
    else:
        errors.extend(
            _bluetooth_input_errors(
                path,
                outputs,
                expected_data_uuid,
                expected_offsets,
                expected_data_conversion,
                expected_mapping,
            )
        )
    errors.extend(
        _bluetooth_output_errors(
            path,
            root,
            bluetooth_id,
            expected_config_uuid,
            expected_config_conversion,
            expected_mode,
            valid_modes,
        )
    )
    return errors


def _bluetooth_input_errors(
    path: str,
    outputs: list[ET.Element],
    expected_data_uuid: str | None,
    expected_offsets: set[int] | None,
    expected_conversion: str | None,
    expected_mapping: dict[int, str] | None,
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    time_outputs = [output for output in outputs if output.attrib.get("extra") == "time"]
    if len(time_outputs) != 1:
        errors.append(
            ValidationError(
                f'{path}: expected exactly one bluetooth <output extra="time"> mapping to CH0'
            )
        )
    else:
        time_output = time_outputs[0]
        if _text(time_output) != "CH0":
            errors.append(ValidationError(f"{path}: app-managed time output must map to CH0"))
        if expected_data_uuid and time_output.attrib.get("char") != expected_data_uuid:
            errors.append(
                ValidationError(
                    f"{path}: bluetooth time output char UUID must be {expected_data_uuid}"
                )
            )
        if "offset" in time_output.attrib:
            errors.append(
                ValidationError(f"{path}: app-managed time output must not have an offset")
            )

    data_outputs = [output for output in outputs if output.attrib.get("extra") != "time"]
    offsets: list[int] = []
    channels: list[str] = []
    actual_mapping: dict[int, str] = {}
    for output in data_outputs:
        channel = _text(output)
        if channel:
            channels.append(channel)
        if expected_data_uuid and output.attrib.get("char") != expected_data_uuid:
            errors.append(
                ValidationError(
                    f"{path}: bluetooth input char UUID for {channel or '<unnamed>'} "
                    f"must be {expected_data_uuid}"
                )
            )
        if expected_conversion and output.attrib.get("conversion") != expected_conversion:
            errors.append(
                ValidationError(
                    f"{path}: expected data conversion {expected_conversion} for "
                    f"{channel or '<unnamed>'} (got {output.attrib.get('conversion')!r})"
                )
            )
        offset = output.attrib.get("offset")
        if offset is None:
            errors.append(
                ValidationError(
                    f"{path}: missing required bluetooth output offset for "
                    f"{_text(output) or '<unnamed>'}"
                )
            )
            continue
        try:
            parsed_offset = int(offset)
            offsets.append(parsed_offset)
            if channel and parsed_offset not in actual_mapping:
                actual_mapping[parsed_offset] = channel
        except ValueError:
            errors.append(ValidationError(f"{path}: invalid bluetooth output offset: {offset!r}"))
    duplicates = sorted({offset for offset in offsets if offsets.count(offset) > 1})
    if duplicates:
        errors.append(ValidationError(f"{path}: duplicate bluetooth output offsets: {duplicates}"))
    duplicate_channels = sorted({channel for channel in channels if channels.count(channel) > 1})
    if duplicate_channels:
        errors.append(
            ValidationError(f"{path}: duplicate bluetooth output channels: {duplicate_channels}")
        )
    if expected_offsets is not None and offsets and set(offsets) != expected_offsets:
        errors.append(
            ValidationError(
                f"{path}: expected data offsets {sorted(expected_offsets)} "
                f"(got {sorted(set(offsets))})"
            )
        )
    if expected_mapping is not None and actual_mapping != expected_mapping:
        errors.append(
            ValidationError(
                f"{path}: bluetooth offset-to-channel mapping must be "
                f"{sorted(expected_mapping.items())} (got {sorted(actual_mapping.items())})"
            )
        )
    return errors


def _bluetooth_output_errors(
    path: str,
    root: ET.Element,
    bluetooth_id: str | None,
    expected_config_uuid: str | None,
    expected_conversion: str | None,
    expected_mode: int | None,
    valid_modes: set[int] | None,
) -> list[ValidationError]:
    output = _child(root, "output")
    if output is None:
        return [ValidationError(f"{path}: missing <output> (used to push config to device)")]
    bluetooth_outputs = _children(output, "bluetooth")
    if len(bluetooth_outputs) != 1:
        return [
            ValidationError(
                f"{path}: expected exactly one <output><bluetooth> block "
                f"(found {len(bluetooth_outputs)})"
            )
        ]
    bluetooth = bluetooth_outputs[0]
    errors: list[ValidationError] = []
    if bluetooth_id and bluetooth.attrib.get("id") != bluetooth_id:
        errors.append(
            ValidationError(f"{path}: bluetooth id mismatch between <input> and <output>")
        )
    configs = _children(bluetooth, "config")
    if len(configs) != 1:
        message = f"{path}: expected exactly one <output><bluetooth><config> (found {len(configs)})"
        return errors + [ValidationError(message)]
    config = configs[0]
    if expected_conversion and config.attrib.get("conversion") != expected_conversion:
        errors.append(
            ValidationError(
                f"{path}: expected config conversion {expected_conversion} "
                f"(got {config.attrib.get('conversion')!r})"
            )
        )
    char = config.attrib.get("char")
    if not char:
        errors.append(ValidationError(f"{path}: <config> missing required attribute char"))
    elif expected_config_uuid and char != expected_config_uuid:
        errors.append(ValidationError(f"{path}: config char UUID must be {expected_config_uuid}"))
    raw_value = _text(config)
    if raw_value is None:
        errors.append(ValidationError(f"{path}: <config> must have a numeric value"))
    else:
        try:
            value = float(raw_value)
        except ValueError:
            errors.append(ValidationError(f"{path}: <config> value is not numeric: {raw_value!r}"))
        else:
            if not math.isfinite(value):
                errors.append(ValidationError(f"{path}: <config> value must be finite"))
            elif valid_modes is not None and (
                not value.is_integer() or int(value) not in valid_modes
            ):
                errors.append(ValidationError(f"{path}: <config> value must be an active mode ID"))
            elif expected_mode is not None and int(value) != expected_mode:
                errors.append(
                    ValidationError(
                        f"{path}: <config> value must match filename mode {expected_mode}"
                    )
                )
    return errors


def validate_phyphox(
    path: str | Path,
    expected_data_uuid: str | None = None,
    expected_config_uuid: str | None = None,
    expected_offsets: set[int] | None = None,
    expected_data_conversion: str | None = None,
    expected_config_conversion: str | None = None,
    expected_mapping: dict[int, str] | None = None,
    expected_mode: int | None = None,
    valid_modes: set[int] | None = None,
) -> list[ValidationError]:
    """Validate the core Arduino phyphox XML contract using defusedxml."""

    if any(
        value is None
        for value in (
            expected_data_uuid,
            expected_config_uuid,
            expected_offsets,
            expected_data_conversion,
            expected_config_conversion,
        )
    ):
        try:
            from .contract import load_contract

            expectations = contract_expectations(load_contract(), path)
            expected_data_uuid = expected_data_uuid or expectations["expected_data_uuid"]
            expected_config_uuid = expected_config_uuid or expectations["expected_config_uuid"]
            expected_offsets = expected_offsets or expectations["expected_offsets"]
            expected_data_conversion = (
                expected_data_conversion or expectations["expected_data_conversion"]
            )
            expected_config_conversion = (
                expected_config_conversion or expectations["expected_config_conversion"]
            )
            expected_mapping = expected_mapping or expectations["expected_mapping"]
            expected_mode = (
                expected_mode if expected_mode is not None else expectations["expected_mode"]
            )
            valid_modes = valid_modes or expectations["valid_modes"]
        except (KeyError, TypeError, ValueError):
            # Preserve the useful structural checks when an isolated caller has
            # no checkout contract available.
            pass
    if expected_mapping is None and expected_offsets is not None:
        expected_mapping = {
            offset: f"CH{index}" for index, offset in enumerate(sorted(expected_offsets), start=1)
        }
    source = str(path)
    try:
        root = ET.parse(path).getroot()
    except OSError as error:
        return [ValidationError(f"{source}: cannot read file: {error}")]
    except DefusedXmlException as error:
        return [ValidationError(f"{source}: XML parse error: unsafe XML rejected: {error}")]
    except ET.ParseError as error:
        return [ValidationError(f"{source}: XML parse error: {error}")]
    errors, continue_validation = _root_errors(source, root)
    if not continue_validation:
        return errors
    container_names, container_errors = _container_errors(source, root)
    errors.extend(container_errors)
    unknown = sorted(set(_references(root)) - set(container_names))
    if unknown:
        errors.append(
            ValidationError(f"{source}: references unknown data containers: {', '.join(unknown)}")
        )
    errors.extend(
        _bluetooth_errors(
            source,
            root,
            expected_data_uuid,
            expected_config_uuid,
            expected_offsets,
            expected_data_conversion,
            expected_config_conversion,
            expected_mapping,
            expected_mode,
            valid_modes,
        )
    )
    return errors
