from __future__ import annotations

import json
import math
import shutil
import subprocess

import pytest

from curious_signals.contract import load_contract
from tests.conftest import REPO_ROOT


@pytest.fixture(scope="module")
def preview_modes():
    node = shutil.which("node")
    assert node, "Preview fixture checks require Node.js 22 or newer."
    version = subprocess.run([node, "--version"], check=True, capture_output=True, text=True)
    major = int(version.stdout.strip().removeprefix("v").split(".")[0])
    assert major >= 22, (
        f"Preview fixture checks require Node.js >=22; found {version.stdout.strip()}."
    )
    result = subprocess.run(
        [node, str(REPO_ROOT / "tests/preview/evaluate.cjs")],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_evaluated_preview_modes_match_contract_channel_shapes(preview_modes) -> None:
    active = load_contract()["modes"]["active"]
    assert [mode["id"] for mode in preview_modes] == [mode["id"] for mode in active]
    for preview, mode in zip(preview_modes, active, strict=True):
        channel_count = sum(
            channel != "CH1" and meaning != "not available"
            for channel, meaning in mode["channels"].items()
        )
        assert len(preview["series"]) == channel_count
        assert len(preview["units"]) == channel_count


def test_every_cached_fixture_value_preserves_the_original_trace(preview_modes) -> None:
    # Every original 121-point trace from demo/demo.js at 7170a5409d710de8d3297bd837da75d12e5f95c2.
    # Absolute tolerance admits platform Math.sin rounding, far below displayed precision.
    original = json.loads((REPO_ROOT / "tests/preview/fixture_values.json").read_text())
    for mode in preview_modes:
        assert mode["cached"] and mode["frozen"]
        assert all(len(values) == 121 for values in mode["values"])
        assert all(math.isfinite(value) for values in mode["values"] for value in values)
        for values, expected in zip(mode["values"], original[str(mode["id"])], strict=True):
            assert values == pytest.approx(expected, rel=0, abs=1e-12)
        for values, bounds in zip(mode["values"], mode["ranges"], strict=True):
            assert bounds[0] < min(values) <= max(values) < bounds[1]
        if mode["id"] != 5:
            assert all(bounds == mode["ranges"][0] for bounds in mode["ranges"])


def test_temperature_and_humidity_keep_separate_units_and_axes(preview_modes) -> None:
    mode = next(mode for mode in preview_modes if mode["id"] == 5)
    assert mode["units"] == ["°C", "%"]
    assert mode["series"] == ["temperature", "humidity"]
    assert mode["ranges"][0][1] < mode["ranges"][1][0]


def test_every_mode_preserves_channel_labels_and_units(preview_modes) -> None:
    expected = {
        1: (["x", "y", "z", "magnitude"], ["m/s²"] * 4),
        2: (["x", "y", "z", "magnitude"], ["rad/s"] * 4),
        3: (["x", "y", "z", "magnitude"], ["µT"] * 4),
        4: (["pressure"], ["hPa"]),
        5: (["temperature", "humidity"], ["°C", "%"]),
        6: (["ambient", "red", "green", "blue"], ["a.u."] * 4),
        9: (["A0", "A1", "A2"], ["ADC"] * 3),
    }
    assert {mode["id"] for mode in preview_modes} == set(expected)
    for mode in preview_modes:
        assert (mode["series"], mode["units"]) == expected[mode["id"]]
