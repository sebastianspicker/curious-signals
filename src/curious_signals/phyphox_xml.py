"""Defused XML plausibility checks for core and astronomy phyphox experiments."""

from __future__ import annotations

import math
from collections.abc import Iterator
from pathlib import Path

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

from .protocol import Protocol


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


def _root_errors(path: str, root: ET.Element) -> tuple[list[str], bool]:
    if _local_name(root.tag) != "phyphox":
        return [f"{path}: root element must be <phyphox> (got <{_local_name(root.tag)}>)"], False
    errors: list[str] = []
    if not root.attrib.get("version"):
        errors.append(f"{path}: <phyphox> missing required attribute version")
    for name in ("title", "category", "description", "data-containers", "input", "views"):
        if _child(root, name) is None:
            errors.append(f"{path}: missing required top-level <{name}> element")
    return errors, True


def _container_errors(path: str, root: ET.Element) -> tuple[list[str], list[str]]:
    containers = _child(root, "data-containers")
    if containers is None:
        return [], []
    names: list[str] = []
    errors: list[str] = []
    for container in _children(containers, "container"):
        name = _text(container)
        if name is None:
            errors.append(f"{path}: <data-containers><container> must have non-empty text")
        else:
            names.append(name)
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        errors.append(f"{path}: duplicate <container> names: {', '.join(duplicates)}")
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
    path: str, root: ET.Element, protocol: Protocol, expected_mode: int | None
) -> list[str]:
    input_element = _child(root, "input")
    if input_element is None:
        return []
    bluetooth_inputs = _children(input_element, "bluetooth")
    if len(bluetooth_inputs) != 1:
        return [
            f"{path}: expected exactly one <input><bluetooth> block (found {len(bluetooth_inputs)})"
        ]
    bluetooth = bluetooth_inputs[0]
    bluetooth_id = bluetooth.attrib.get("id")
    errors: list[str] = []
    if not bluetooth_id:
        errors.append(f"{path}: <input><bluetooth> missing required attribute id")
    outputs = _children(bluetooth, "output")
    if len(outputs) < 2:
        errors.append(f"{path}: <input><bluetooth> must contain <output> mappings")
    else:
        errors.extend(_bluetooth_input_errors(path, outputs, protocol))
    errors.extend(_bluetooth_output_errors(path, root, bluetooth_id, protocol, expected_mode))
    return errors


def _bluetooth_input_errors(path: str, outputs: list[ET.Element], protocol: Protocol) -> list[str]:
    data_uuid = protocol.data_char_uuid
    conversion = protocol.data_encoding
    errors: list[str] = []
    time_outputs = [output for output in outputs if output.attrib.get("extra") == "time"]
    if len(time_outputs) != 1:
        errors.append(
            f'{path}: expected exactly one bluetooth <output extra="time"> mapping to CH0'
        )
    else:
        time_output = time_outputs[0]
        if _text(time_output) != "CH0":
            errors.append(f"{path}: app-managed time output must map to CH0")
        if time_output.attrib.get("char") != data_uuid:
            errors.append(f"{path}: bluetooth time output char UUID must be {data_uuid}")
        if "offset" in time_output.attrib:
            errors.append(f"{path}: app-managed time output must not have an offset")

    data_outputs = [output for output in outputs if output.attrib.get("extra") != "time"]
    offsets: list[int] = []
    channels: list[str] = []
    actual_mapping: dict[int, str] = {}
    for output in data_outputs:
        channel = _text(output)
        if channel:
            channels.append(channel)
        if output.attrib.get("char") != data_uuid:
            errors.append(
                f"{path}: bluetooth input char UUID for {channel or '<unnamed>'} "
                f"must be {data_uuid}"
            )
        if output.attrib.get("conversion") != conversion:
            errors.append(
                f"{path}: expected data conversion {conversion} for "
                f"{channel or '<unnamed>'} (got {output.attrib.get('conversion')!r})"
            )
        offset = output.attrib.get("offset")
        if offset is None:
            errors.append(
                f"{path}: missing required bluetooth output offset for "
                f"{_text(output) or '<unnamed>'}"
            )
            continue
        try:
            parsed_offset = int(offset)
            offsets.append(parsed_offset)
            if channel and parsed_offset not in actual_mapping:
                actual_mapping[parsed_offset] = channel
        except ValueError:
            errors.append(f"{path}: invalid bluetooth output offset: {offset!r}")
    duplicates = sorted({offset for offset in offsets if offsets.count(offset) > 1})
    if duplicates:
        errors.append(f"{path}: duplicate bluetooth output offsets: {duplicates}")
    duplicate_channels = sorted({channel for channel in channels if channels.count(channel) > 1})
    if duplicate_channels:
        errors.append(f"{path}: duplicate bluetooth output channels: {duplicate_channels}")
    expected_offsets = set(protocol.data_offsets)
    if offsets and set(offsets) != expected_offsets:
        errors.append(
            f"{path}: expected data offsets {sorted(expected_offsets)} (got {sorted(set(offsets))})"
        )
    expected_mapping = {
        offset: f"CH{index}" for index, offset in enumerate(protocol.data_offsets, start=1)
    }
    if actual_mapping != expected_mapping:
        errors.append(
            f"{path}: bluetooth offset-to-channel mapping must be "
            f"{sorted(expected_mapping.items())} (got {sorted(actual_mapping.items())})"
        )
    return errors


def _bluetooth_output_errors(
    path: str,
    root: ET.Element,
    bluetooth_id: str | None,
    protocol: Protocol,
    expected_mode: int | None,
) -> list[str]:
    output = _child(root, "output")
    if output is None:
        return [f"{path}: missing <output> (used to push config to device)"]
    bluetooth_outputs = _children(output, "bluetooth")
    if len(bluetooth_outputs) != 1:
        return [
            f"{path}: expected exactly one <output><bluetooth> block "
            f"(found {len(bluetooth_outputs)})"
        ]
    bluetooth = bluetooth_outputs[0]
    errors: list[str] = []
    if bluetooth_id and bluetooth.attrib.get("id") != bluetooth_id:
        errors.append(f"{path}: bluetooth id mismatch between <input> and <output>")
    configs = _children(bluetooth, "config")
    if len(configs) != 1:
        return errors + [
            f"{path}: expected exactly one <output><bluetooth><config> (found {len(configs)})"
        ]
    config = configs[0]
    conversion = protocol.config_encoding
    if config.attrib.get("conversion") != conversion:
        errors.append(
            f"{path}: expected config conversion {conversion} "
            f"(got {config.attrib.get('conversion')!r})"
        )
    char = config.attrib.get("char")
    if not char:
        errors.append(f"{path}: <config> missing required attribute char")
    elif char != protocol.config_char_uuid:
        errors.append(f"{path}: config char UUID must be {protocol.config_char_uuid}")
    raw_value = _text(config)
    if raw_value is None:
        errors.append(f"{path}: <config> must have a numeric value")
        return errors
    try:
        value = float(raw_value)
    except ValueError:
        errors.append(f"{path}: <config> value is not numeric: {raw_value!r}")
        return errors
    valid_modes = {mode.id for mode in protocol.modes}
    if not math.isfinite(value):
        errors.append(f"{path}: <config> value must be finite")
    elif not value.is_integer() or int(value) not in valid_modes:
        errors.append(f"{path}: <config> value must be an active mode ID")
    elif expected_mode is not None and int(value) != expected_mode:
        errors.append(f"{path}: <config> value must match filename mode {expected_mode}")
    return errors


def check_core_experiment(
    path: Path, protocol: Protocol, *, expected_mode: int | None
) -> list[str]:
    """Return errors where one core phyphox file breaks the XML or protocol contract."""

    source = str(path)
    try:
        root = ET.parse(path).getroot()
    except OSError as error:
        return [f"{source}: cannot read file: {error}"]
    except DefusedXmlException as error:
        return [f"{source}: XML parse error: unsafe XML rejected: {error}"]
    except ET.ParseError as error:
        return [f"{source}: XML parse error: {error}"]
    errors, continue_validation = _root_errors(source, root)
    if not continue_validation:
        return errors
    container_names, container_errors = _container_errors(source, root)
    errors.extend(container_errors)
    unknown = sorted(set(_references(root)) - set(container_names))
    if unknown:
        errors.append(f"{source}: references unknown data containers: {', '.join(unknown)}")
    errors.extend(_bluetooth_errors(source, root, protocol, expected_mode))
    return errors


def check_astronomy_experiment(path: Path) -> list[str]:
    """Return XML safety and English, German, French locale errors for one astronomy file."""

    try:
        root = ET.parse(path).getroot()
    except OSError as error:
        return [f"{path}: cannot read XML: {error}"]
    except DefusedXmlException as error:
        return [f"{path}: unsafe XML rejected: {error}"]
    except ET.ParseError as error:
        return [f"{path}: XML parse error: {error}"]
    errors: list[str] = []
    if _local_name(root.tag) != "phyphox":
        errors.append(f"{path}: root element must be <phyphox>")
    if root.attrib.get("locale") != "en":
        errors.append(f"{path}: root locale must be en")
    locales = {
        element.attrib.get("locale") for element in root.findall("./translations/translation")
    }
    missing = {"de", "fr"} - locales
    if missing:
        errors.append(f"{path}: missing translation locale(s): {', '.join(sorted(missing))}")
    return errors
