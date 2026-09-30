from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT


def test_toolchain_manifest_preserves_supported_target_and_pins() -> None:
    toolchain = json.loads((REPO_ROOT / "scripts/arduino-toolchain.json").read_text())
    assert toolchain == {
        "fqbn": "arduino:mbed_nano:nano33ble",
        "core": "arduino:mbed_nano@4.5.0",
        "libraries": [
            "ArduinoBLE@1.5.0",
            "Arduino_LSM9DS1@1.1.1",
            "Arduino_HTS221@1.0.0",
            "Arduino_LPS22HB@1.0.2",
            "Arduino_APDS9960@1.0.4",
        ],
    }


@pytest.fixture()
def arduino_stub(tmp_path: Path) -> tuple[dict[str, str], Path]:
    toolchain = json.loads((REPO_ROOT / "scripts/arduino-toolchain.json").read_text())
    core_name, core_version = toolchain["core"].split("@")
    (tmp_path / "core.json").write_text(
        json.dumps({"platforms": [{"id": core_name, "installed_version": core_version}]})
    )
    (tmp_path / "libraries.json").write_text(
        json.dumps(
            {
                "installed_libraries": [
                    {"library": dict(zip(("name", "version"), pin.split("@"), strict=True))}
                    for pin in toolchain["libraries"]
                ]
            }
        )
    )
    stub = tmp_path / "arduino-cli"
    stub.write_text(
        f"#!{sys.executable}\n"
        "import json, pathlib, sys\n"
        "root = pathlib.Path(__file__).parent\n"
        "with (root / 'calls.jsonl').open('a') as log:\n"
        "    log.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "if sys.argv[1:3] == ['core', 'list']: print((root / 'core.json').read_text())\n"
        "if sys.argv[1:3] == ['lib', 'list']: print((root / 'libraries.json').read_text())\n"
    )
    stub.chmod(0o755)
    return dict(os.environ, PATH=f"{tmp_path}{os.pathsep}{os.environ['PATH']}"), tmp_path


def compile_sketch(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "scripts/compile-arduino.sh"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_compile_only_checks_installed_versions_then_compiles(arduino_stub) -> None:
    env, root = arduino_stub

    result = compile_sketch(env)

    assert result.returncode == 0, result.stderr
    calls = [json.loads(line) for line in (root / "calls.jsonl").read_text().splitlines()]
    assert [call[:2] for call in calls[:2]] == [["core", "list"], ["lib", "list"]]
    assert calls[2] == [
        "compile",
        "--fqbn",
        "arduino:mbed_nano:nano33ble",
        "arduino/phyphox_ble_sense",
    ]


@pytest.mark.parametrize("fault", ["core", "library", "duplicate", "invalid_json", "invalid_shape"])
def test_compile_rejects_wrong_or_ambiguous_installations(arduino_stub, fault: str) -> None:
    env, root = arduino_stub
    if fault == "core":
        (root / "core.json").write_text('{"platforms": []}')
    elif fault == "invalid_json":
        (root / "core.json").write_text("not json")
    elif fault == "invalid_shape":
        (root / "core.json").write_text("[]")
    else:
        path = root / "libraries.json"
        data = json.loads(path.read_text())
        if fault == "library":
            data["installed_libraries"][0]["library"]["version"] = "0.0.0"
        else:
            data["installed_libraries"].append(data["installed_libraries"][0])
        path.write_text(json.dumps(data))

    result = compile_sketch(env)

    assert result.returncode != 0
    assert "Traceback" not in result.stderr
    calls = [json.loads(line) for line in (root / "calls.jsonl").read_text().splitlines()]
    assert not any(call[0] == "compile" for call in calls)
    assert not any("install" in call or "update-index" in call for call in calls)


def test_provision_installs_manifest_pins_and_verifies(arduino_stub) -> None:
    env, root = arduino_stub
    toolchain = json.loads((REPO_ROOT / "scripts/arduino-toolchain.json").read_text())

    result = subprocess.run(
        [sys.executable, "scripts/arduino_toolchain.py", "provision"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    calls = [json.loads(line) for line in (root / "calls.jsonl").read_text().splitlines()]
    assert calls[:3] == [
        ["core", "update-index"],
        ["core", "install", toolchain["core"]],
        ["lib", "install", *toolchain["libraries"]],
    ]
    assert [call[:2] for call in calls[3:]] == [["core", "list"], ["lib", "list"]]
