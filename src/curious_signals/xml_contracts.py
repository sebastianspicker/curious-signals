"""Defused XML plausibility checks for generated core phyphox experiments."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException


@dataclass(frozen=True)
class ValidationError:
    message: str


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
            )
        )
    errors.extend(
        _bluetooth_output_errors(
            path,
            root,
            bluetooth_id,
            expected_config_uuid,
            expected_config_conversion,
        )
    )
    return errors


def _bluetooth_input_errors(
    path: str,
    outputs: list[ET.Element],
    expected_data_uuid: str | None,
    expected_offsets: set[int] | None,
    expected_conversion: str | None,
) -> list[ValidationError]:
    data_chars: set[str] = set()
    offsets: list[int] = []
    has_time = False
    errors: list[ValidationError] = []
    for output in outputs:
        if output.attrib.get("extra") == "time":
            has_time = True
            continue
        if char := output.attrib.get("char"):
            data_chars.add(char)
        if expected_conversion and output.attrib.get("conversion") != expected_conversion:
            errors.append(
                ValidationError(
                    f"{path}: expected data conversion {expected_conversion} "
                    f"(got {output.attrib.get('conversion')!r})"
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
            offsets.append(int(offset))
        except ValueError:
            errors.append(ValidationError(f"{path}: invalid bluetooth output offset: {offset!r}"))
    if not has_time:
        errors.append(ValidationError(f'{path}: missing bluetooth <output extra="time"> mapping'))
    if len(data_chars) != 1:
        errors.append(
            ValidationError(f"{path}: expected exactly one data characteristic UUID in inputs")
        )
    if expected_data_uuid and data_chars and data_chars != {expected_data_uuid}:
        errors.append(
            ValidationError(f"{path}: bluetooth input char UUID must be {expected_data_uuid}")
        )
    duplicates = sorted({offset for offset in offsets if offsets.count(offset) > 1})
    if duplicates:
        errors.append(ValidationError(f"{path}: duplicate bluetooth output offsets: {duplicates}"))
    if expected_offsets is not None and offsets and set(offsets) != expected_offsets:
        errors.append(
            ValidationError(
                f"{path}: expected data offsets {sorted(expected_offsets)} "
                f"(got {sorted(set(offsets))})"
            )
        )
    return errors


def _bluetooth_output_errors(
    path: str,
    root: ET.Element,
    bluetooth_id: str | None,
    expected_config_uuid: str | None,
    expected_conversion: str | None,
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
    value = _text(config)
    if value is None:
        errors.append(ValidationError(f"{path}: <config> must have a numeric value"))
    else:
        try:
            float(value)
        except ValueError:
            errors.append(ValidationError(f"{path}: <config> value is not numeric: {value!r}"))
    return errors


def validate_phyphox(
    path: str | Path,
    expected_data_uuid: str | None = None,
    expected_config_uuid: str | None = None,
    expected_offsets: set[int] | None = None,
    expected_data_conversion: str | None = None,
    expected_config_conversion: str | None = None,
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

            contract = load_contract()
            bluetooth = contract["bluetooth"]
            frame = contract["frame"]
            expected_data_uuid = expected_data_uuid or bluetooth["data_char_uuid"]
            expected_config_uuid = expected_config_uuid or bluetooth["config_char_uuid"]
            expected_offsets = expected_offsets or {
                field["offset"] for field in frame["data"]["fields"]
            }
            expected_data_conversion = expected_data_conversion or frame["data"]["encoding"]
            expected_config_conversion = expected_config_conversion or frame["config"]["encoding"]
        except (KeyError, TypeError, ValueError):
            # Preserve the useful structural checks when an isolated caller has
            # no checkout contract available.
            pass
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
        )
    )
    return errors
