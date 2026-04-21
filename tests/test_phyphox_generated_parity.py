"""Parity tests for generated phyphox artifacts."""

from __future__ import annotations

import difflib
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPO_ROOT / "src" / "phyphox"
EXPERIMENTS_DIR = REPO_ROOT / "experiments"


def _source_files() -> list[Path]:
    return sorted(SOURCE_DIR.glob("*.phyphox.xml"))


def test_generated_files_match_sources(tmp_path: Path) -> None:
    outdir = tmp_path / "phyphox-build"
    subprocess.run(
        ["bash", str(REPO_ROOT / "scripts" / "build-phyphox.sh"), str(outdir)],
        check=True,
        cwd=REPO_ROOT,
        text=True,
    )

    generated_files = sorted(outdir.glob("*.phyphox"))
    source_files = _source_files()
    repo_generated_files = sorted(EXPERIMENTS_DIR.glob("*.phyphox"))

    assert [path.name for path in generated_files] == [path.name for path in repo_generated_files]
    assert [path.name.replace(".xml", "") for path in source_files] == [
        path.name for path in repo_generated_files
    ]

    for repo_path in repo_generated_files:
        built_path = outdir / repo_path.name
        repo_text = repo_path.read_text(encoding="utf-8")
        built_text = built_path.read_text(encoding="utf-8")
        if repo_text != built_text:
            diff = "\n".join(
                difflib.unified_diff(
                    repo_text.splitlines(),
                    built_text.splitlines(),
                    fromfile=str(repo_path),
                    tofile=str(built_path),
                    lineterm="",
                )
            )
            raise AssertionError(f"{repo_path.name} does not match build output:\n{diff}")
