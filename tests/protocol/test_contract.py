from __future__ import annotations

import json
from copy import deepcopy

import pytest
from defusedxml import ElementTree as ET

from curious_signals.protocol import contract_errors, load_protocol, read_contract
from tests.conftest import CONTRACT_PATH, CORE_ARTIFACT_DIR, CORE_SOURCE_DIR, REPO_ROOT


def test_contract_schema_and_declared_inventory_are_valid() -> None:
    protocol = load_protocol(CONTRACT_PATH)

    assert contract_errors(read_contract(CONTRACT_PATH)) == []
    assert protocol.device_name == "phyphox-sense"
    assert protocol.data_encoding == "float32LittleEndian"
    assert protocol.data_offsets == (0, 4, 8, 12, 16)
    assert protocol.reserved_modes == (7, 8)
    assert len(protocol.modes) == 7


def test_version_one_compatibility_baseline_is_explicit() -> None:
    contract = read_contract(CONTRACT_PATH)
    protocol = load_protocol(CONTRACT_PATH)

    assert protocol.device_name == "phyphox-sense"
    assert contract["bluetooth"] == {
        "service_uuid": "cddf0001-30f7-4671-8b43-5e40ba53514a",
        "data_char_uuid": "cddf1002-30f7-4671-8b43-5e40ba53514a",
        "config_char_uuid": "cddf1003-30f7-4671-8b43-5e40ba53514a",
    }
    assert (protocol.service_uuid, protocol.data_char_uuid, protocol.config_char_uuid) == tuple(
        contract["bluetooth"].values()
    )
    assert protocol.sample_period_ms == 50
    assert contract["frame"]["data"]["byte_length"] == 20
    assert contract["frame"]["data"]["access"] == ["notify"]
    assert contract["frame"]["config"]["access"] == ["read", "write"]
    assert contract["frame"]["config"]["selection"] == {
        "rounding": "nearest_integer",
        "minimum": 0.5,
        "maximum_exclusive": 9.5,
        "invalid_behavior": "keep_active_mode",
    }
    assert [mode.id for mode in protocol.modes] == [1, 2, 3, 4, 5, 6, 9]
    assert protocol.default_mode == 1
    assert protocol.reserved_modes == (7, 8)


def test_contract_conforms_to_firmware_sources_artifacts_and_preview() -> None:
    protocol = load_protocol(CONTRACT_PATH)
    firmware = (REPO_ROOT / "arduino" / "phyphox_ble_sense" / "phyphox_ble_sense.ino").read_text(
        encoding="utf-8"
    )
    preview = (REPO_ROOT / "demo" / "fixtures.js").read_text(encoding="utf-8")
    artifacts = {path.name for path in CORE_ARTIFACT_DIR.glob("*.phyphox")}
    sources = {path.name.removesuffix(".xml") for path in CORE_SOURCE_DIR.glob("*.phyphox.xml")}

    for uuid in (protocol.service_uuid, protocol.data_char_uuid, protocol.config_char_uuid):
        assert uuid in firmware
    assert set(protocol.experiments) == artifacts == sources
    for mode in protocol.modes:
        source_config = ET.parse(CORE_SOURCE_DIR / f"{mode.experiment}.xml").find(
            "./output/bluetooth/config"
        )
        artifact_config = ET.parse(CORE_ARTIFACT_DIR / mode.experiment).find(
            "./output/bluetooth/config"
        )
        assert source_config is not None and artifact_config is not None
        assert source_config.text == artifact_config.text == f"{mode.id}.0"
        assert source_config.attrib["char"] == artifact_config.attrib["char"]
        assert source_config.attrib["char"] == protocol.config_char_uuid
        assert f"id: {mode.id}" in preview
        assert mode.channels


def test_contributor_docs_name_the_contract_device_and_uuids() -> None:
    protocol = load_protocol(CONTRACT_PATH)
    root_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    firmware_readme = (REPO_ROOT / "arduino" / "phyphox_ble_sense" / "README.md").read_text(
        encoding="utf-8"
    )

    assert f"`{protocol.device_name}`" in root_readme
    assert f"`{protocol.device_name}`" in firmware_readme
    for uuid in (protocol.service_uuid, protocol.data_char_uuid, protocol.config_char_uuid):
        assert f"`{uuid}`" in firmware_readme


def test_contract_rejects_missing_protocol_field() -> None:
    contract = read_contract(CONTRACT_PATH)
    contract["device"].pop("name")

    assert contract_errors(contract)


@pytest.mark.parametrize(
    ("path", "invalid"),
    [
        (("modes", "active", 0, "id"), []),
        (("modes", "reserved"), [{}]),
        (("frame", "data", "fields", 0, "offset"), []),
        (("frame", "data", "access"), [1]),
        (("frame", "config", "selection", "minimum"), {}),
        (("modes", "active", 0, "channels"), []),
    ],
)
def test_malformed_contract_types_return_diagnostics_without_crashing(
    path: tuple[object, ...], invalid: object
) -> None:
    contract = deepcopy(read_contract(CONTRACT_PATH))
    target: object = contract
    for key in path[:-1]:
        target = target[key]  # type: ignore[index]
    target[path[-1]] = invalid  # type: ignore[index]

    assert contract_errors(contract)


@pytest.mark.parametrize(
    ("path", "invalid", "expected"),
    [
        (("schema_version",), True, "schema_version"),
        (("frame", "data", "encoding"), "float32BigEndian", "encoding"),
        (("frame", "data", "access"), ["read"], "access"),
        (("frame", "config", "access"), ["write"], "access"),
        (("frame", "config", "selection", "rounding"), "floor", "rounding"),
        (
            ("frame", "config", "selection", "invalid_behavior"),
            "select_default",
            "invalid_behavior",
        ),
        (("modes", "active", 0, "id"), 0, "positive"),
        (("modes", "active", 0, "id"), 10, "selection range"),
        (("modes", "active", 0, "name"), "Bad Name", "identifier"),
        (("modes", "active", 0, "experiment"), "../bad.phyphox", "filename"),
    ],
)
def test_contract_rejects_unsupported_schema_values(
    path: tuple[object, ...], invalid: object, expected: str
) -> None:
    contract = deepcopy(read_contract(CONTRACT_PATH))
    target: object = contract
    for key in path[:-1]:
        target = target[key]  # type: ignore[index]
    target[path[-1]] = invalid  # type: ignore[index]

    assert expected in "\n".join(contract_errors(contract))


@pytest.mark.parametrize("offset", [2, 8])
def test_contract_rejects_overlapping_or_gapped_field_spans(offset: int) -> None:
    contract = deepcopy(read_contract(CONTRACT_PATH))
    contract["frame"]["data"]["fields"][1]["offset"] = offset

    errors = "\n".join(contract_errors(contract))

    assert "contiguous" in errors
    assert "non-overlapping" in errors


def test_contract_file_is_valid_json() -> None:
    assert json.loads(CONTRACT_PATH.read_text(encoding="utf-8")) == read_contract(CONTRACT_PATH)
