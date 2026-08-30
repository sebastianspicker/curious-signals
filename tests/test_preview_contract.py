from __future__ import annotations

import re

from curious_signals.contract import load_contract
from tests.conftest import REPO_ROOT


def test_preview_is_deterministic_and_does_not_claim_ble_or_network_access() -> None:
    preview = (REPO_ROOT / "demo" / "demo.js").read_text(encoding="utf-8")

    assert "function fixtureValue" in preview
    assert "Math.random" not in preview
    assert "Bluetooth" not in preview
    assert "fetch(" not in preview
    assert "WebSocket" not in preview


def test_preview_modes_match_contract_channel_shapes() -> None:
    preview = (REPO_ROOT / "demo" / "demo.js").read_text(encoding="utf-8")
    contract = load_contract()

    for mode in contract["modes"]["active"]:
        section = re.search(rf"\{{ id: {mode['id']},(.*?) \}},", preview)
        assert section is not None
        series = re.search(r"series: \[(.*?)\]", section.group(1))
        assert series is not None
        channel_count = sum(
            channel != "CH1" and meaning != "not available"
            for channel, meaning in mode["channels"].items()
        )
        assert len(re.findall(r'"[^"]+"', series.group(1))) == channel_count
