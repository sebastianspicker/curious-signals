from __future__ import annotations

import os
import shlex
import shutil
from pathlib import Path

import pytest

from curious_signals.checkout import Checkout

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "protocol" / "contract.json"
CORE_SOURCE_DIR = REPO_ROOT / "src" / "phyphox"
CORE_ARTIFACT_DIR = REPO_ROOT / "experiments"
ASTRONOMY_DIR = CORE_ARTIFACT_DIR / "astronomy"


@pytest.fixture()
def xmllint_executable() -> str:
    executable = shutil.which("xmllint")
    assert executable is not None, "Tests require xmllint (libxml2 utilities) on PATH."
    return executable


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


@pytest.fixture()
def checkout_copy(tmp_path: Path) -> Checkout:
    """Return a disposable checkout holding the protocol, core sources, and experiments."""

    root = tmp_path / "checkout"
    shutil.copytree(REPO_ROOT / "protocol", root / "protocol")
    shutil.copytree(CORE_SOURCE_DIR, root / "src" / "phyphox")
    shutil.copytree(CORE_ARTIFACT_DIR, root / "experiments")
    return Checkout(root)


def install_fake_xmllint(
    directory: Path, monkeypatch: pytest.MonkeyPatch, *, delegate_to: str | None
) -> Path:
    """Put a recording xmllint first on PATH and return its call log.

    With ``delegate_to`` the fake forwards to that executable; otherwise it fails.
    """

    directory.mkdir(parents=True, exist_ok=True)
    log = directory / "xmllint-calls.log"
    forward = (
        f'exec {shlex.quote(delegate_to)} "$@"'
        if delegate_to
        else 'echo "fake xmllint must not run" >&2; exit 97'
    )
    script = directory / "xmllint"
    script.write_text(
        f'#!/bin/sh\nprintf "%s\\n" "$*" >> {shlex.quote(str(log))}\n{forward}\n',
        encoding="utf-8",
    )
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{directory}{os.pathsep}{os.environ.get('PATH', '')}")
    return log


def error_text(errors: object) -> str:
    return "\n".join(str(error) for error in errors).lower()
