from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT


@pytest.fixture()
def security_checkout(tmp_path: Path) -> Path:
    shutil.copytree(REPO_ROOT / "scripts", tmp_path / "scripts")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def run_gate(root: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "scripts/secret-scan.sh"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_scan_errors_fail_closed(security_checkout: Path) -> None:
    binaries = security_checkout / "bin"
    binaries.mkdir()
    stub = binaries / "rg"
    stub.write_text("#!/bin/sh\nexit 2\n", encoding="utf-8")
    stub.chmod(0o755)
    env = dict(os.environ, PATH=f"{binaries}{os.pathsep}{os.environ['PATH']}")

    result = run_gate(security_checkout, env)

    assert result.returncode == 2
    assert "scan is incomplete" in result.stderr
    assert not result.stdout.rstrip().endswith("OK")


def test_scans_tracked_and_untracked_files_and_redacts_matches(security_checkout: Path) -> None:
    # Deliberately synthetic; assemble at runtime so the repository scan stays clean.
    token = "gh" + "p_" + "A" * 36
    tracked = security_checkout / "tracked.txt"
    tracked.write_text("clean\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=security_checkout, check=True)
    tracked.write_text(token, encoding="utf-8")
    untracked = security_checkout / "odd name\nwith newline.txt"
    untracked.write_text(token, encoding="utf-8")

    result = run_gate(security_checkout)

    assert result.returncode == 1
    assert "tracked.txt:1" in result.stdout
    assert f"{untracked.name}:1" in result.stdout
    assert token not in result.stdout + result.stderr


def test_clean_checkout_and_empty_matches_succeed(security_checkout: Path) -> None:
    (security_checkout / "ordinary.txt").write_text("Classroom notes", encoding="utf-8")

    result = run_gate(security_checkout)

    assert result.returncode == 0, result.stderr
    assert result.stdout.rstrip().endswith("OK")


def test_files_after_first_batch_are_scanned(security_checkout: Path) -> None:
    for index in range(140):
        (security_checkout / f"notes-{index:03}.txt").write_text("clean", encoding="utf-8")
    token = "gh" + "p_" + "B" * 36
    (security_checkout / "zz-last.txt").write_text(token, encoding="utf-8")

    result = run_gate(security_checkout)

    assert result.returncode == 1
    assert "zz-last.txt:1" in result.stdout
    assert token not in result.stdout + result.stderr
