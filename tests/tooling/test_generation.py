from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from curious_signals import contract as contract_module
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


def test_build_and_validate_reject_unsafe_xml_before_invoking_xmllint(
    tmp_path, monkeypatch
) -> None:
    source_dir = tmp_path / "sources"
    shutil.copytree(CORE_SOURCE_DIR, source_dir)
    sources = sorted(source_dir.glob("*.phyphox.xml"))
    sources[0].write_text(
        sources[0]
        .read_text(encoding="utf-8")
        .replace("<phyphox", '<phyphox xml:base="https://example.invalid/"', 1),
        encoding="utf-8",
    )
    monkeypatch.setattr(workflows, "_core_sources", lambda: sources)
    monkeypatch.setattr(
        workflows, "_core_includes", lambda: sorted((source_dir / "includes").glob("*.xml"))
    )
    monkeypatch.setattr(workflows, "core_include_dir", lambda: source_dir / "includes")

    def unexpected_xmllint(arguments: list[str]) -> subprocess.CompletedProcess[str]:
        raise AssertionError(f"xmllint invoked before preflight completed: {arguments}")

    monkeypatch.setattr(workflows, "_run_xmllint", unexpected_xmllint)

    with pytest.raises(workflows.ToolError, match="xml:base"):
        workflows.build(tmp_path / "output")
    assert "xml:base" in "\n".join(workflows.validate())


def test_validate_expands_each_source_once_and_loads_contract_once(monkeypatch) -> None:
    expansion_calls: list[list[str]] = []
    load_calls = 0
    original_load = contract_module.load_contract

    def counted_load():
        nonlocal load_calls
        load_calls += 1
        return original_load()

    def fake_xmllint(arguments: list[str]) -> subprocess.CompletedProcess[str]:
        stdout = ""
        if "--xinclude" in arguments:
            expansion_calls.append(arguments)
            source = Path(arguments[-1])
            artifact = CORE_ARTIFACT_DIR / source.name.removesuffix(".xml")
            stdout = artifact.read_text(encoding="utf-8")
        return subprocess.CompletedProcess(arguments, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(workflows, "load_contract", counted_load)
    monkeypatch.setattr(contract_module, "load_contract", counted_load)
    monkeypatch.setattr(workflows, "_require_xmllint", lambda: "xmllint")
    monkeypatch.setattr(workflows, "_run_xmllint", fake_xmllint)

    assert workflows.validate() == []
    assert len(expansion_calls) == len(list(CORE_SOURCE_DIR.glob("*.phyphox.xml"))) == 7
    assert load_calls == 1
