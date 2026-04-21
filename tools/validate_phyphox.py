#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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


def _load_expected_uuids() -> tuple[str | None, str | None, str | None, list[ValidationError]]:
    errors: list[ValidationError] = []
    constants_path = REPO_ROOT / "experiments" / "phyphox_constants.json"
    sketch_path = REPO_ROOT / "arduino" / "phyphox_ble_sense" / "phyphox_ble_sense.ino"

    constants_service_uuid: str | None = None
    constants_data_uuid: str | None = None
    constants_config_uuid: str | None = None
    sketch_service_uuid: str | None = None
    sketch_data_uuid: str | None = None
    sketch_config_uuid: str | None = None

    try:
        constants = json.loads(constants_path.read_text(encoding="utf-8"))
        bluetooth = constants.get("bluetooth", {})
        constants_service_uuid = bluetooth.get("service_uuid")
        constants_data_uuid = bluetooth.get("data_char_uuid")
        constants_config_uuid = bluetooth.get("config_char_uuid")
        for key in ("service_uuid", "data_char_uuid", "config_char_uuid"):
            if not bluetooth.get(key):
                errors.append(
                    ValidationError(f"{constants_path}: missing required bluetooth.{key}")
                )
    except OSError as e:
        errors.append(ValidationError(f"{constants_path}: cannot read file: {e}"))
    except json.JSONDecodeError as e:
        errors.append(ValidationError(f"{constants_path}: invalid JSON: {e}"))

    try:
        for line in sketch_path.read_text(encoding="utf-8").splitlines():
            match = SKETCH_UUID_RE.match(line.strip())
            if not match:
                continue
            key, value = match.groups()
            if key == "kPhyphoxServiceUuid":
                sketch_service_uuid = value
            elif key == "kDataCharUuid":
                sketch_data_uuid = value
            elif key == "kConfigCharUuid":
                sketch_config_uuid = value
    except OSError as e:
        errors.append(ValidationError(f"{sketch_path}: cannot read file: {e}"))

    if not sketch_service_uuid:
        errors.append(ValidationError(f"{sketch_path}: missing required kPhyphoxServiceUuid"))
    if not sketch_data_uuid:
        errors.append(ValidationError(f"{sketch_path}: missing required kDataCharUuid"))
    if not sketch_config_uuid:
        errors.append(ValidationError(f"{sketch_path}: missing required kConfigCharUuid"))

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

    return (
        constants_service_uuid or sketch_service_uuid,
        constants_data_uuid or sketch_data_uuid,
        constants_config_uuid or sketch_config_uuid,
        errors,
    )


def _load_expected_modes() -> list[ValidationError]:
    errors: list[ValidationError] = []
    constants_path = REPO_ROOT / "experiments" / "phyphox_constants.json"
    sketch_path = REPO_ROOT / "arduino" / "phyphox_ble_sense" / "phyphox_ble_sense.ino"
    source_dir = REPO_ROOT / "src" / "phyphox"

    constants_modes: dict[str, int] = {}
    sketch_modes: dict[str, int] = {}
    source_mode_ids: set[int] = set()

    try:
        constants = json.loads(constants_path.read_text(encoding="utf-8"))
        raw_modes = constants.get("modes", {})
        if not raw_modes:
            errors.append(ValidationError(f"{constants_path}: missing required modes object"))
        for name in MODE_NAME_MAP.values():
            value = raw_modes.get(name)
            if not isinstance(value, int):
                errors.append(ValidationError(f"{constants_path}: missing required modes.{name}"))
                continue
            constants_modes[name] = value
    except OSError as e:
        errors.append(ValidationError(f"{constants_path}: cannot read file: {e}"))
        return errors
    except json.JSONDecodeError as e:
        errors.append(ValidationError(f"{constants_path}: invalid JSON: {e}"))
        return errors

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
        errors.append(ValidationError(f"{sketch_path}: cannot read file: {e}"))
        return errors

    for name in MODE_NAME_MAP.values():
        if name not in sketch_modes:
            errors.append(ValidationError(f"{sketch_path}: missing required mode {name}"))

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
        try:
            source_mode_ids.add(int(float(config.text.strip())))
        except ValueError:
            errors.append(ValidationError(f"{path}: invalid output bluetooth config value"))

    if constants_modes and sketch_modes and constants_modes != sketch_modes:
        errors.append(ValidationError(f"{constants_path}: mode IDs do not match {sketch_path}"))
    if constants_modes and set(constants_modes.values()) != source_mode_ids:
        errors.append(
            ValidationError(f"{constants_path}: mode IDs do not match source phyphox config values")
        )

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

    if _local_name(root.tag) != "phyphox":
        errors.append(
            ValidationError(
                f"{path}: root element must be <phyphox> (got <{_local_name(root.tag)}>)"
            )
        )
        return errors

    version = root.attrib.get("version")
    if not version:
        errors.append(ValidationError(f"{path}: <phyphox> missing required attribute version"))

    required_top = ["title", "category", "description", "data-containers", "input", "views"]
    for name in required_top:
        if _child(root, name) is None:
            errors.append(ValidationError(f"{path}: missing required top-level <{name}> element"))

    containers_el = _child(root, "data-containers")
    container_names: list[str] = []
    if containers_el is not None:
        for c in _children(containers_el, "container"):
            name = _text(c)
            if not name:
                errors.append(
                    ValidationError(
                        f"{path}: <data-containers><container> must have non-empty text"
                    )
                )
                continue
            container_names.append(name)

    container_set = set(container_names)
    if len(container_set) != len(container_names):
        seen: set[str] = set()
        dups: set[str] = set()
        for n in container_names:
            if n in seen:
                dups.add(n)
            seen.add(n)
        errors.append(
            ValidationError(f"{path}: duplicate <container> names: {', '.join(sorted(dups))}")
        )

    referenced: set[str] = set()

    input_el = _child(root, "input")
    if input_el is not None:
        for bt in _children(input_el, "bluetooth"):
            for out in _children(bt, "output"):
                t = _text(out)
                if t:
                    referenced.add(t)

    views_el = _child(root, "views")
    if views_el is not None:
        for el in views_el.iter():
            if _local_name(el.tag) == "input":
                t = _text(el)
                if t:
                    referenced.add(t)

    analysis_el = _child(root, "analysis")
    if analysis_el is not None:
        for el in analysis_el.iter():
            lname = _local_name(el.tag)
            if lname in ("input", "output"):
                t = _text(el)
                if t:
                    referenced.add(t)

    export_el = _child(root, "export")
    if export_el is not None:
        for data in export_el.iter():
            if _local_name(data.tag) != "data":
                continue
            t = _text(data)
            if t:
                referenced.add(t)

    unknown = sorted(n for n in referenced if n not in container_set)
    if unknown:
        errors.append(
            ValidationError(f"{path}: references unknown data containers: {', '.join(unknown)}")
        )

    if input_el is not None:
        bt_inputs = _children(input_el, "bluetooth")
        if len(bt_inputs) != 1:
            errors.append(
                ValidationError(
                    (
                        f"{path}: expected exactly one <input><bluetooth> block "
                        f"(found {len(bt_inputs)})"
                    )
                )
            )
        else:
            bt = bt_inputs[0]
            bt_id = bt.attrib.get("id")
            if not bt_id:
                errors.append(
                    ValidationError(f"{path}: <input><bluetooth> missing required attribute id")
                )

            outs = _children(bt, "output")
            if len(outs) < 2:
                errors.append(
                    ValidationError(f"{path}: <input><bluetooth> must contain <output> mappings")
                )
            else:
                data_chars: set[str] = set()
                offsets: set[int] = set()
                has_extra_time = False
                for o in outs:
                    target_name = _text(o)
                    extra = o.attrib.get("extra")
                    if extra == "time":
                        has_extra_time = True
                        continue
                    ch = o.attrib.get("char")
                    if ch:
                        data_chars.add(ch)
                    off = o.attrib.get("offset")
                    if off is None:
                        missing_name = target_name or "<unnamed>"
                        message = (
                            f"{path}: missing required bluetooth output offset for {missing_name}"
                        )
                        errors.append(ValidationError(message))
                        continue
                    try:
                        offsets.add(int(off))
                    except ValueError:
                        errors.append(
                            ValidationError(f"{path}: invalid bluetooth output offset: {off!r}")
                        )

                if not has_extra_time:
                    errors.append(
                        ValidationError(f'{path}: missing bluetooth <output extra="time"> mapping')
                    )
                if len(data_chars) != 1:
                    errors.append(
                        ValidationError(
                            f"{path}: expected exactly one data characteristic UUID in inputs"
                        )
                    )
                if expected_data_uuid and data_chars and data_chars != {expected_data_uuid}:
                    errors.append(
                        ValidationError(
                            f"{path}: bluetooth input char UUID must be {expected_data_uuid}"
                        )
                    )
                if offsets and offsets != EXPECTED_OFFSETS:
                    errors.append(
                        ValidationError(
                            (
                                f"{path}: expected float32 offsets "
                                f"{sorted(EXPECTED_OFFSETS)} (got {sorted(offsets)})"
                            )
                        )
                    )

            out_el = _child(root, "output")
            if out_el is None:
                errors.append(
                    ValidationError(f"{path}: missing <output> (used to push config to device)")
                )
            else:
                bt_outs = _children(out_el, "bluetooth")
                if len(bt_outs) != 1:
                    errors.append(
                        ValidationError(
                            (
                                f"{path}: expected exactly one <output><bluetooth> block "
                                f"(found {len(bt_outs)})"
                            )
                        )
                    )
                else:
                    bt_out = bt_outs[0]
                    if bt_id and bt_out.attrib.get("id") != bt_id:
                        errors.append(
                            ValidationError(
                                f"{path}: bluetooth id mismatch between <input> and <output>"
                            )
                        )

                    configs = _children(bt_out, "config")
                    if len(configs) != 1:
                        errors.append(
                            ValidationError(
                                (
                                    f"{path}: expected exactly one "
                                    f"<output><bluetooth><config> "
                                    f"(found {len(configs)})"
                                )
                            )
                        )
                    else:
                        cfg = configs[0]
                        if cfg.attrib.get("conversion") != "float32LittleEndian":
                            errors.append(
                                ValidationError(
                                    (
                                        f"{path}: expected config conversion "
                                        "float32LittleEndian "
                                        f"(got {cfg.attrib.get('conversion')!r})"
                                    )
                                )
                            )
                        config_char = cfg.attrib.get("char")
                        if not config_char:
                            errors.append(
                                ValidationError(f"{path}: <config> missing required attribute char")
                            )
                        elif expected_config_uuid and config_char != expected_config_uuid:
                            errors.append(
                                ValidationError(
                                    f"{path}: config char UUID must be {expected_config_uuid}"
                                )
                            )
                        v = _text(cfg)
                        if v is None:
                            errors.append(
                                ValidationError(f"{path}: <config> must have a numeric value")
                            )
                        else:
                            try:
                                float(v)
                            except ValueError:
                                errors.append(
                                    ValidationError(f"{path}: <config> value is not numeric: {v!r}")
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
