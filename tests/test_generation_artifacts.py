from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from curious_signals import workflows
from curious_signals.postprocess import postprocess
from tests.conftest import CORE_ARTIFACT_DIR, CORE_SOURCE_DIR, REPO_ROOT


def test_postprocess_is_deterministic_and_preserves_experiment_content() -> None:
    source = (
        '<phyphox xmlns:xi="http://www.w3.org/2001/XInclude" xml:base="source.xml">'
        '<title>Stable</title><container unit="m/s²">CH1</container></phyphox>'
    )

    result = postprocess(source)

    assert result == postprocess(source)
    assert "xml:base" not in result
    assert "xmlns:xi" not in result
    assert '<container unit="m/s²">CH1</container>' in result


def test_core_sources_and_committed_artifacts_have_byte_parity_when_xmllint_is_available() -> None:
    if shutil.which("xmllint") is None:
        pytest.skip("xmllint is required for generated-artifact parity")

    result = subprocess.run(
        ["python3", "-m", "curious_signals", "check-generated"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert {path.name for path in CORE_SOURCE_DIR.glob("*.phyphox.xml")} == {
        f"{path.name}.xml" for path in CORE_ARTIFACT_DIR.glob("*.phyphox")
    }


@pytest.mark.skipif(shutil.which("xmllint") is None, reason="xmllint is unavailable")
@pytest.mark.parametrize("inventory_change", ["missing", "extra", "invalid"])
def test_build_rejects_bad_source_inventory_or_content_before_writing(
    tmp_path: Path, monkeypatch, inventory_change: str
) -> None:
    source_dir = tmp_path / "sources"
    shutil.copytree(CORE_SOURCE_DIR, source_dir)
    sources = sorted(source_dir.glob("*.phyphox.xml"))
    if inventory_change == "missing":
        sources.pop()
    elif inventory_change == "extra":
        rogue = source_dir / "rogue.phyphox.xml"
        rogue.write_text(sources[0].read_text(encoding="utf-8"), encoding="utf-8")
        sources.append(rogue)
    else:
        sources[0].write_text(
            sources[0].read_text(encoding="utf-8").replace('version="1.7"', "", 1),
            encoding="utf-8",
        )
    monkeypatch.setattr(workflows, "_core_sources", lambda: sorted(sources))
    destination = tmp_path / "output"

    with pytest.raises(workflows.ToolError):
        workflows.build(destination)

    assert not destination.exists()
