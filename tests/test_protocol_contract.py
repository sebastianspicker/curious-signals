from __future__ import annotations

import json
from copy import deepcopy

import pytest
from defusedxml import ElementTree as ET

from curious_signals import repository_contracts
from curious_signals.contract import load_contract, validate_contract
from tests.conftest import CORE_ARTIFACT_DIR, CORE_SOURCE_DIR, REPO_ROOT


def test_contract_schema_and_declared_inventory_are_valid() -> None:
    contract = load_contract()

    assert validate_contract(contract) == []
    assert contract["device"]["name"] == "phyphox-sense"
    assert contract["frame"]["data"]["encoding"] == "float32LittleEndian"
    assert [field["offset"] for field in contract["frame"]["data"]["fields"]] == [0, 4, 8, 12, 16]
    assert contract["modes"]["reserved"] == [7, 8]
    assert len(contract["modes"]["active"]) == 7


def test_version_one_compatibility_baseline_is_explicit() -> None:
    contract = load_contract()

    assert contract["device"]["name"] == "phyphox-sense"
    assert contract["bluetooth"] == {
        "service_uuid": "cddf0001-30f7-4671-8b43-5e40ba53514a",
        "data_char_uuid": "cddf1002-30f7-4671-8b43-5e40ba53514a",
        "config_char_uuid": "cddf1003-30f7-4671-8b43-5e40ba53514a",
    }
    assert contract["frame"]["sample_period_ms"] == 50
    assert contract["frame"]["data"]["byte_length"] == 20
    assert contract["frame"]["data"]["access"] == ["notify"]
    assert contract["frame"]["config"]["access"] == ["read", "write"]
    assert contract["frame"]["config"]["selection"] == {
        "rounding": "nearest_integer",
        "minimum": 0.5,
        "maximum_exclusive": 9.5,
        "invalid_behavior": "keep_active_mode",
    }
    assert [mode["id"] for mode in contract["modes"]["active"]] == [1, 2, 3, 4, 5, 6, 9]
    assert contract["modes"]["default"] == 1
    assert contract["modes"]["reserved"] == [7, 8]


def test_contract_conforms_to_firmware_sources_artifacts_and_preview() -> None:
    contract = load_contract()
    firmware = (REPO_ROOT / "arduino" / "phyphox_ble_sense" / "phyphox_ble_sense.ino").read_text(
        encoding="utf-8"
    )
    preview = (REPO_ROOT / "demo" / "demo.js").read_text(encoding="utf-8")
    artifacts = {path.name for path in CORE_ARTIFACT_DIR.glob("*.phyphox")}
    sources = {path.name.removesuffix(".xml") for path in CORE_SOURCE_DIR.glob("*.phyphox.xml")}

    for uuid in contract["bluetooth"].values():
        assert uuid in firmware
    assert {mode["experiment"] for mode in contract["modes"]["active"]} == artifacts == sources
    for mode in contract["modes"]["active"]:
        source_config = ET.parse(CORE_SOURCE_DIR / f"{mode['experiment']}.xml").find(
            "./output/bluetooth/config"
        )
        artifact_config = ET.parse(CORE_ARTIFACT_DIR / mode["experiment"]).find(
            "./output/bluetooth/config"
        )
        assert source_config is not None and artifact_config is not None
        assert source_config.text == artifact_config.text == f"{mode['id']}.0"
        assert source_config.attrib["char"] == artifact_config.attrib["char"]
        assert source_config.attrib["char"] == contract["bluetooth"]["config_char_uuid"]
        assert f"id: {mode['id']}" in preview
        assert mode["channels"]


def test_contract_rejects_missing_protocol_field() -> None:
    contract = load_contract()
    contract["device"].pop("name")

    assert validate_contract(contract)


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
    contract = deepcopy(load_contract())
    target: object = contract
    for key in path[:-1]:
        target = target[key]  # type: ignore[index]
    target[path[-1]] = invalid  # type: ignore[index]

    assert validate_contract(contract)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda text: text.replace('BLE.setLocalName("phyphox-sense");', "", 1),
        lambda text: text.replace(
            "writeFloat32LE(payload, sizeof(payload), 4, ch2);",
            "writeFloat32LE(payload, sizeof(payload), 5, ch2);",
            1,
        ),
        lambda text: text.replace("buf[offset + 3] =", "buf[offset + 2] =", 1),
    ],
)
def test_firmware_conformance_rejects_name_payload_and_codec_drift(
    tmp_path, monkeypatch, mutation
) -> None:
    sketch = REPO_ROOT / "arduino" / "phyphox_ble_sense" / "phyphox_ble_sense.ino"
    candidate = tmp_path / sketch.name
    candidate.write_text(mutation(sketch.read_text(encoding="utf-8")), encoding="utf-8")
    monkeypatch.setattr(repository_contracts, "firmware_path", lambda: candidate)

    assert repository_contracts.validate_repository_contract(load_contract())


def test_contract_file_is_valid_json() -> None:
    contract_path = REPO_ROOT / "protocol" / "contract.json"

    assert json.loads(contract_path.read_text(encoding="utf-8")) == load_contract(contract_path)
