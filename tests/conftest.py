from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE_DIR = REPO_ROOT / "src" / "phyphox"
CORE_ARTIFACT_DIR = REPO_ROOT / "experiments"
ASTRONOMY_DIR = CORE_ARTIFACT_DIR / "astronomy"


@pytest.fixture()
def valid_phyphox_xml() -> str:
    return """\
<phyphox version="1.7" locale="en">
  <title>Test</title><category>Test</category><description>Test</description>
  <data-containers>
    <container>CH0</container><container>CH1</container><container>CH2</container>
    <container>CH3</container><container>CH4</container><container>CH5</container>
  </data-containers>
  <input><bluetooth id="Sense" mode="notification">
    <output extra="time">CH0</output>
    <output char="data" conversion="float32LittleEndian" offset="0">CH1</output>
    <output char="data" conversion="float32LittleEndian" offset="4">CH2</output>
    <output char="data" conversion="float32LittleEndian" offset="8">CH3</output>
    <output char="data" conversion="float32LittleEndian" offset="12">CH4</output>
    <output char="data" conversion="float32LittleEndian" offset="16">CH5</output>
  </bluetooth></input>
  <output><bluetooth id="Sense">
    <config char="config" conversion="float32LittleEndian">1</config>
  </bluetooth></output>
  <views><view label="Test"><graph label="Test">
    <input axis="x">CH1</input><input axis="y">CH2</input>
  </graph></view></views>
</phyphox>
"""


@pytest.fixture()
def phyphox_file(tmp_path: Path):
    def write(xml: str) -> Path:
        target = tmp_path / "experiment.phyphox"
        target.write_text(xml, encoding="utf-8")
        return target

    return write


def error_text(errors: object) -> str:
    return "\n".join(str(error) for error in errors).lower()
