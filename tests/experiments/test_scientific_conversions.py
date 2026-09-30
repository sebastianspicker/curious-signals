from __future__ import annotations

import math

import pytest
from defusedxml import ElementTree as ET

from tests.conftest import ASTRONOMY_DIR, CORE_ARTIFACT_DIR, CORE_SOURCE_DIR
from tests.experiments.scientific_formulas import scalar_output

# Preserve the existing classroom scales and their precision. These examples
# check numerical transformations, not physical sensor accuracy or calibration.
CORE_CASES = [
    ("accelerometer", range(2, 6), "m/s²", [(-1, -9.81), (0, 0), (2, 19.62)]),
    ("gyroscope", range(2, 6), "rad/s", [(-180, -math.pi), (0, 0), (90, math.pi / 2)]),
    ("analog_input", range(2, 5), "mV", [(0, 0), (500, 1613), (1023, 3300.198)]),
    ("pressure", range(2, 3), "hPa", [(0, 0), (101.325, 1013.25)]),
]


@pytest.mark.parametrize("generated", [False, True], ids=["source", "artifact"])
@pytest.mark.parametrize(("name", "channels", "unit", "examples"), CORE_CASES)
def test_core_conversion_values_channels_units_and_exports(
    generated: bool, name: str, channels: range, unit: str, examples: list
) -> None:
    path = (
        CORE_ARTIFACT_DIR / f"{name}_plot_v1-2.phyphox"
        if generated
        else CORE_SOURCE_DIR / f"{name}_plot_v1-2.phyphox.xml"
    )
    root = ET.parse(path).getroot()
    for channel in channels:
        source, output = f"CH{channel}", f"CH{channel}_norm"
        for raw, expected in examples:
            assert scalar_output(root, output, {source: raw}) == pytest.approx(expected, rel=1e-6)
        values = [e for e in root.findall("./views/view/value") if e.findtext("input") == output]
        assert values and all(e.get("unit") == unit for e in values)
        graphs = [
            e
            for e in root.findall("./views/view/graph")
            if any(i.text == output for i in e.findall("input[@axis='y']"))
        ]
        assert graphs and all(e.get("unitY") == unit for e in graphs)
        exports = [e for e in root.findall("./export/set/data") if e.text == output]
        assert exports and all(f"({unit})" in e.attrib["name"] for e in exports)


@pytest.mark.parametrize(
    ("name", "mapping"),
    [
        ("temperature", {"CH2": "°C", "CH3": "%"}),
        ("magnetometer", {f"CH{i}": "µT" for i in range(2, 6)}),
        ("light", {f"CH{i}": "a.u." for i in range(2, 6)}),
    ],
)
def test_unscaled_core_channels_keep_each_display_and_export_unit(name, mapping) -> None:
    root = ET.parse(CORE_ARTIFACT_DIR / f"{name}_plot_v1-2.phyphox").getroot()
    assert not root.findall("./analysis/formula")
    for channel, unit in mapping.items():
        values = [e for e in root.findall("./views/view/value") if e.findtext("input") == channel]
        assert values and all(e.get("unit") == unit for e in values)
        exports = [e for e in root.findall("./export/set/data") if e.text == channel]
        assert exports and all(f"({unit})" in e.attrib["name"] for e in exports)


@pytest.mark.parametrize(
    ("filename", "pairs"),
    [
        ("greenhouse", [("tempRaw1", "tempCal1"), ("tempRaw2", "tempCal2")]),
        ("pt-star", [("tempRaw", "tempCal"), ("pRaw", "pCal")]),
        ("missiontomars", [("st_tempRaw", "st_tempCal"), ("st_pRaw", "st_p")]),
        ("tidal-locking", [("tempRaw1", "tempCal1"), ("tempRaw2", "tempCal2")]),
    ],
)
def test_sensortag_hundredth_unit_conversions(filename, pairs) -> None:
    root = ET.parse(ASTRONOMY_DIR / f"{filename}.phyphox").getroot()
    for source, output in pairs:
        for raw, expected in [(-1250, -12.5), (0, 0), (101325, 1013.25)]:
            assert scalar_output(root, output, {source: raw}) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("filename", "pairs"),
    [
        ("ir-dist_habitable", [("T_IR_raw", "T_IR_cal"), ("T_amb_raw", "T_amb_cal")]),
        (
            "tidal-locking",
            [(f"{kind}Raw{i}", f"{kind}Cal{i}") for i in (1, 2) for kind in ("amb", "obj")],
        ),
    ],
)
def test_infrared_raw_temperature_decoding(filename, pairs) -> None:
    root = ET.parse(ASTRONOMY_DIR / f"{filename}.phyphox").getroot()
    for source, output in pairs:
        for raw, expected in [(-640, -5), (0, 0), (3203, 25)]:
            assert scalar_output(root, output, {source: raw}) == expected


@pytest.mark.parametrize(
    ("filename", "source", "output"),
    [
        ("albedo", "st_RawInt", "st_amplitude"),
        ("transitmethode", "RawInt", "amplitude"),
        ("tidal-locking", "RawInt1", "amplitude1"),
        ("tidal-locking", "RawInt2", "amplitude2"),
    ],
)
def test_optical_exponent_mantissa_decoding(filename, source, output) -> None:
    root = ET.parse(ASTRONOMY_DIR / f"{filename}.phyphox").getroot()
    for raw, lux in [(0, 0), (100, 1), (0x1001, 0.02), (0x3123, 23.28), (0xFFFF, 1341849.6)]:
        assert scalar_output(root, output, {source: raw}) == pytest.approx(lux)


@pytest.mark.parametrize(
    ("filename", "count", "stop", "output", "period"),
    [
        ("greenhouse", "count", "tmax", "t", 1 / 60),
        ("pt-star", "count", "tmax", "t", 1 / 60),
        ("missiontomars", "st_count", "st_tmax", "st_t", 0.1),
        ("albedo", "st_countI", "st_tmax", "st_t", 0.8),
        ("transitmethode", "countI", "tmax", "t", 0.8),
        ("tidal-locking", "count", "tmax", "t", 1),
        ("tidal-locking", "count1", "tmax1", "t1", 0.3),
        ("tidal-locking", "countI2", "tmax2", "t2", 0.8),
    ],
)
def test_nominal_time_axes_keep_zero_origin_and_sample_intervals(
    filename, count, stop, output, period
):
    root = ET.parse(ASTRONOMY_DIR / f"{filename}.phyphox").getroot()
    ramps = [node for node in root.findall("./analysis/ramp") if node.findtext("output") == output]
    assert len(ramps) == 1
    roles = {node.get("as"): node for node in ramps[0].findall("input")}
    assert roles["start"].get("type") == "value" and float(roles["start"].text) == 0
    assert roles["stop"].text == stop and roles["length"].text == count
    for length in (1, 2, 61):
        assert scalar_output(root, stop, {count: length}) == pytest.approx((length - 1) * period)


def test_transit_depth_radius_ratio_and_duration_examples() -> None:
    root = ET.parse(ASTRONOMY_DIR / "transitmethode.phyphox").getroot()
    values = {"max_amplitude": 1000, "min_amplitude": 990, "R_star": 10}
    assert scalar_output(root, "transit_depth", values) == 1
    assert scalar_output(root, "R_planet", values) == 1
    assert scalar_output(root, "Quot_R", values) == 10
    assert scalar_output(root, "avg_transit_time", {f"don{i}": i for i in range(1, 6)}) == 3
    years = dict(zip(("dt01", "dt12", "dt23", "dt34", "dt45"), (8, 9, 10, 11, 12), strict=True))
    assert scalar_output(root, "avg_year_duration", years) == 10


def test_albedo_both_paths_preserve_percentage_definition() -> None:
    root = ET.parse(ASTRONOMY_DIR / "albedo.phyphox").getroot()
    for prefix in ("phone", "st"):
        for minimum, expected in [(100, 0), (75, 25), (0, 100)]:
            values = {f"{prefix}_max_amplitude": 100, f"{prefix}_min_amplitude": minimum}
            assert scalar_output(root, f"{prefix}_depth", values) == expected


@pytest.mark.parametrize("filename", ["owon_digital_multimeter-debug", "transitmethode"])
def test_owon_decimal_and_prefix_scale_decoding(filename) -> None:
    root = ET.parse(ASTRONOMY_DIR / f"{filename}.phyphox").getroot()
    for bitmask, decimal, prefix in [(32, 1, 1), (34, 0.01, 1), (24, 1, 0.001), (40, 1, 1000)]:
        assert scalar_output(root, "18decfac", {"18bitmask": bitmask}) == pytest.approx(decimal)
        assert scalar_output(root, "18prefac", {"18bitmask": bitmask}) == pytest.approx(prefix)
