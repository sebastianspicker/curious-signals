from __future__ import annotations

import os
import shutil
import subprocess

from tests.conftest import REPO_ROOT


def test_actual_firmware_with_controlled_ble_sensors_and_clock(tmp_path) -> None:
    compiler = shutil.which(os.environ.get("CXX", "c++"))
    assert compiler is not None, "Host firmware tests require a C++17 compiler (CXX or c++)."
    executable = tmp_path / "firmware-behavior"
    build = subprocess.run(
        [
            compiler,
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            "-I",
            str(REPO_ROOT / "tests/firmware/doubles"),
            str(REPO_ROOT / "tests/firmware/behavior.cpp"),
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
