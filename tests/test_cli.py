from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from hashlib import sha256

import pytest

from tests.conftest import REPO_ROOT


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "curious_signals", *arguments],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is unavailable")
def test_validate_cli_succeeds_for_current_repository() -> None:
    result = run_cli("validate")

    assert result.returncode == 0, result.stderr


def test_cli_rejects_unknown_command_without_traceback() -> None:
    result = run_cli("unknown-command")

    assert result.returncode != 0
    assert "traceback" not in result.stderr.lower()


def test_make_help_advertises_only_current_entry_points() -> None:
    result = subprocess.run(
        ["make", "help"], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stderr
    assert "ci-local" not in result.stdout
    for target in ("build", "validate", "check-generated", "compile", "security", "ci", "bundle"):
        assert target in result.stdout


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is unavailable")
def test_build_and_bundle_cli_create_requested_outputs(tmp_path) -> None:
    build = run_cli("build", "--output", str(tmp_path / "built"))
    first_archive = tmp_path / "experiments-one.zip"
    second_archive = tmp_path / "experiments-two.zip"
    bundle = run_cli("bundle", "--output", str(first_archive))
    repeated = run_cli("bundle", "--output", str(second_archive))

    assert build.returncode == 0, build.stderr
    assert bundle.returncode == 0, bundle.stderr
    assert repeated.returncode == 0, repeated.stderr
    assert len(list((tmp_path / "built").glob("*.phyphox"))) == 7
    assert (
        sha256(first_archive.read_bytes()).digest() == sha256(second_archive.read_bytes()).digest()
    )
    with zipfile.ZipFile(first_archive) as archive:
        expected = sorted(path.name for path in (REPO_ROOT / "experiments").glob("*.phyphox"))
        assert archive.namelist() == expected
        for info in archive.infolist():
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
            assert (
                archive.read(info.filename)
                == (REPO_ROOT / "experiments" / info.filename).read_bytes()
            )
