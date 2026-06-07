"""Regression tests for repository guardrails and shared contracts."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import validate_phyphox

REPO_ROOT = Path(__file__).resolve().parents[1]
CONSTANTS_PATH = REPO_ROOT / "experiments" / "phyphox_constants.json"
SKETCH_PATH = REPO_ROOT / "arduino" / "phyphox_ble_sense" / "phyphox_ble_sense.ino"
CI_LOCAL_PATH = REPO_ROOT / "scripts" / "ci-local.sh"
SECRET_SCAN_PATH = REPO_ROOT / "scripts" / "secret-scan.sh"
BASH = "/bin/bash"


def test_service_uuid_matches_between_constants_and_firmware() -> None:
    constants = json.loads(CONSTANTS_PATH.read_text(encoding="utf-8"))
    firmware = SKETCH_PATH.read_text(encoding="utf-8")

    assert constants["bluetooth"]["service_uuid"] in firmware


def test_ci_local_checks_generated_files_before_in_place_build(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    bin_dir = tmp_path / "bin"
    log_path = tmp_path / "ci-local.log"
    scripts.mkdir(parents=True)
    bin_dir.mkdir()
    shutil.copy2(CI_LOCAL_PATH, scripts / "ci-local.sh")

    for command in ("ruff", "pytest"):
        tool = bin_dir / command
        tool.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        tool.chmod(0o755)

    for script in (
        "validate-xml.sh",
        "check-generated-clean.sh",
        "build-phyphox.sh",
        "compile-arduino.sh",
        "secret-scan.sh",
        "deps-scan.sh",
        "sast-minimal.sh",
    ):
        (scripts / script).write_text(
            f"#!/usr/bin/env bash\nprintf '%s\\n' {script!r} >> {str(log_path)!r}\n",
            encoding="utf-8",
        )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    result = subprocess.run(
        [BASH, str(scripts / "ci-local.sh")],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    calls = log_path.read_text(encoding="utf-8").splitlines()
    assert calls.index("check-generated-clean.sh") < calls.index("build-phyphox.sh")


def test_build_phyphox_fails_when_source_files_are_missing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "scripts" / "build-phyphox.sh", scripts / "build-phyphox.sh")

    result = subprocess.run(
        [BASH, str(scripts / "build-phyphox.sh")],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "No source files found" in result.stderr


def test_secret_scan_flags_untracked_files() -> None:
    temp_path = REPO_ROOT / ".secret-scan-test.tmp"
    temp_token = "ghp_" + ("1234567890" * 4)[:36]
    temp_path.write_text(f"{temp_token}\n", encoding="utf-8")
    try:
        result = subprocess.run(
            [BASH, str(SECRET_SCAN_PATH)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        temp_path.unlink(missing_ok=True)

    assert result.returncode == 1
    assert str(temp_path.relative_to(REPO_ROOT)) in result.stdout


def test_uuid_loader_requires_all_expected_keys(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    constants_dir = repo_root / "experiments"
    sketch_dir = repo_root / "arduino" / "phyphox_ble_sense"
    constants_dir.mkdir(parents=True)
    sketch_dir.mkdir(parents=True)

    (constants_dir / "phyphox_constants.json").write_text(
        json.dumps(
            {
                "bluetooth": {
                    "data_char_uuid": "cddf1002-30f7-4671-8b43-5e40ba53514a",
                    "config_char_uuid": "cddf1003-30f7-4671-8b43-5e40ba53514a",
                }
            }
        ),
        encoding="utf-8",
    )
    (sketch_dir / "phyphox_ble_sense.ino").write_text(
        "\n".join(
            [
                (
                    "constexpr const char* kPhyphoxServiceUuid = "
                    '"cddf0001-30f7-4671-8b43-5e40ba53514a";'
                ),
                'constexpr const char* kDataCharUuid = "cddf1002-30f7-4671-8b43-5e40ba53514a";',
                'constexpr const char* kConfigCharUuid = "cddf1003-30f7-4671-8b43-5e40ba53514a";',
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(validate_phyphox, "REPO_ROOT", repo_root)

    service_uuid, data_uuid, config_uuid, errors = validate_phyphox._load_expected_uuids()

    assert service_uuid == "cddf0001-30f7-4671-8b43-5e40ba53514a"
    assert data_uuid == "cddf1002-30f7-4671-8b43-5e40ba53514a"
    assert config_uuid == "cddf1003-30f7-4671-8b43-5e40ba53514a"
    assert any("missing required bluetooth.service_uuid" in error.message for error in errors)


def test_constants_json_documents_reserved_modes() -> None:
    constants = json.loads(CONSTANTS_PATH.read_text(encoding="utf-8"))

    assert "reserved_modes" in constants, "phyphox_constants.json must have a 'reserved_modes' key"

    reserved = constants["reserved_modes"]
    assert isinstance(reserved, list), "'reserved_modes' must be a list"
    assert all(isinstance(m, int) for m in reserved), "'reserved_modes' entries must be ints"

    active_modes = set(constants.get("modes", {}).values())
    for m in reserved:
        assert 1 <= m <= 9, f"reserved mode {m} is outside the expected 1..9 range"
        assert m not in active_modes, (
            f"mode {m} appears in both 'modes' and 'reserved_modes'; "
            "a mode cannot be active and reserved at the same time"
        )


def test_firmware_initial_config_matches_default_mode() -> None:
    firmware = SKETCH_PATH.read_text(encoding="utf-8")

    assert "Mode mode = Mode::kAcceleration;" in firmware
    assert "writeFloat32LE(cfg, sizeof(cfg), 0, (float)Mode::kAcceleration);" in firmware


def test_firmware_rejects_fractional_and_reserved_modes_explicitly() -> None:
    firmware = SKETCH_PATH.read_text(encoding="utf-8")

    assert "fabsf(configValue - rounded)" in firmware
    assert "raw > 9" not in firmware
    assert "Accept the full reserved range" not in firmware
    assert "Reserved mode received" not in firmware
