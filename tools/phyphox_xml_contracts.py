"""XML contract checks shared by the phyphox validator facade."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

EXPECTED_OFFSETS = {0, 4, 8, 12, 16}


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _child(parent: ET.Element, name: str) -> ET.Element | None:
    for child in list(parent):
        if _local_name(child.tag) == name:
            return child
    return None


def _children(parent: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in list(parent) if _local_name(child.tag) == name]


def _text(element: ET.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    text = element.text.strip()
    return text if text else None


@dataclass(frozen=True)
class ValidationError:
    message: str


@dataclass
class BluetoothInputState:
    data_chars: set[str]
    offsets: list[int]
    has_extra_time: bool = False


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
    for name in ["title", "category", "description", "data-containers", "input", "views"]:
        if _child(root, name) is None:
            errors.append(ValidationError(f"{path}: missing required top-level <{name}> element"))
    return errors, True


def _container_names(path: str, root: ET.Element) -> tuple[list[str], list[ValidationError]]:
    errors: list[ValidationError] = []
    names: list[str] = []
    containers = _child(root, "data-containers")
    if containers is None:
        return names, errors
    for container in _children(containers, "container"):
        name = _text(container)
        if not name:
            errors.append(
                ValidationError(f"{path}: <data-containers><container> must have non-empty text")
            )
            continue
        names.append(name)
    return names, errors


def _duplicate_container_errors(path: str, names: list[str]) -> list[ValidationError]:
    if len(set(names)) == len(names):
        return []
    seen: set[str] = set()
    duplicates: set[str] = set()
    for name in names:
        if name in seen:
            duplicates.add(name)
        seen.add(name)
    return [
        ValidationError(f"{path}: duplicate <container> names: {', '.join(sorted(duplicates))}")
    ]


def _iter_bluetooth_output_references(bluetooth: ET.Element) -> Iterator[str]:
    for output in _children(bluetooth, "output"):
        if target := _text(output):
            yield target


def _iter_input_references(root: ET.Element) -> Iterator[str]:
    input_element = _child(root, "input")
    if input_element is None:
        return
    for bluetooth in _children(input_element, "bluetooth"):
        yield from _iter_bluetooth_output_references(bluetooth)


def _input_references(root: ET.Element) -> set[str]:
    return set(_iter_input_references(root))


def _section_references(root: ET.Element, parent_name: str, allowed_tags: set[str]) -> set[str]:
    parent = _child(root, parent_name)
    if parent is None:
        return set()
    referenced: set[str] = set()
    for element in parent.iter():
        if _local_name(element.tag) in allowed_tags and (target := _text(element)):
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
        errors.append(
            ValidationError(
                f"{path}: missing required bluetooth output offset for {target_name or '<unnamed>'}"
            )
        )
        return errors
    try:
        state.offsets.append(int(offset))
    except ValueError:
        errors.append(ValidationError(f"{path}: invalid bluetooth output offset: {offset!r}"))
    return errors


def _unknown_reference_errors(
    path: str, referenced: set[str], names: list[str]
) -> list[ValidationError]:
    unknown = sorted(name for name in referenced if name not in set(names))
    return (
        []
        if not unknown
        else [ValidationError(f"{path}: references unknown data containers: {', '.join(unknown)}")]
    )


def _bluetooth_input_contract_errors(
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


def _bluetooth_offset_errors(path: str, offsets: list[int]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    duplicate_offsets = sorted(offset for offset in set(offsets) if offsets.count(offset) > 1)
    if duplicate_offsets:
        errors.append(
            ValidationError(f"{path}: duplicate bluetooth output offsets: {duplicate_offsets}")
        )
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
    errors: list[ValidationError] = []
    state = BluetoothInputState(data_chars=set(), offsets=[])
    for output in outputs:
        errors.extend(_record_bluetooth_output(path, output, state))
    errors.extend(_bluetooth_input_contract_errors(path, state, expected_data_uuid))
    errors.extend(_bluetooth_offset_errors(path, state.offsets))
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
    errors: list[ValidationError] = []
    bluetooth = bluetooth_outputs[0]
    if input_bt_id and bluetooth.attrib.get("id") != input_bt_id:
        errors.append(
            ValidationError(f"{path}: bluetooth id mismatch between <input> and <output>")
        )
    configs = _children(bluetooth, "config")
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
    bluetooth_inputs = _children(input_element, "bluetooth")
    if len(bluetooth_inputs) != 1:
        return [
            ValidationError(
                f"{path}: expected exactly one <input><bluetooth> block "
                f"(found {len(bluetooth_inputs)})"
            )
        ]
    errors: list[ValidationError] = []
    bluetooth = bluetooth_inputs[0]
    bluetooth_id = bluetooth.attrib.get("id")
    if not bluetooth_id:
        errors.append(ValidationError(f"{path}: <input><bluetooth> missing required attribute id"))
    outputs = _children(bluetooth, "output")
    if len(outputs) < 2:
        errors.append(ValidationError(f"{path}: <input><bluetooth> must contain <output> mappings"))
    else:
        errors.extend(_validate_bluetooth_input_outputs(path, outputs, expected_data_uuid))
    errors.extend(_validate_bluetooth_config_output(path, root, bluetooth_id, expected_config_uuid))
    return errors


def validate_phyphox(
    path: str, expected_data_uuid: str | None = None, expected_config_uuid: str | None = None
) -> list[ValidationError]:
    try:
        root = ET.parse(path).getroot()
    except OSError as error:
        return [ValidationError(f"{path}: cannot read file: {error}")]
    except DefusedXmlException as error:
        return [ValidationError(f"{path}: XML parse error: unsafe XML rejected: {error}")]
    except ET.ParseError as error:
        return [ValidationError(f"{path}: XML parse error: {error}")]
    errors, should_continue = _validate_root_contract(path, root)
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
