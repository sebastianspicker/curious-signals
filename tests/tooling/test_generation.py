from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from curious_signals import ToolError
from curious_signals.checkout import Checkout
from curious_signals.generation import build
from curious_signals.validation import validate
from curious_signals.xmllint import strip_xinclude_metadata
from tests.conftest import CORE_ARTIFACT_DIR, CORE_SOURCE_DIR, REPO_ROOT, install_fake_xmllint


def test_strip_xinclude_metadata_is_deterministic_and_preserves_experiment_content() -> None:
    source = (
        '<phyphox xmlns:xi="http://www.w3.org/2001/XInclude" xml:base="source.xml">'
        '<title>Stable</title><container unit="m/s²">CH1</container></phyphox>'
    )

    result = strip_xinclude_metadata(source)

    assert result == strip_xinclude_metadata(source)
    assert "xml:base" not in result
    assert "xmlns:xi" not in result
    assert '<container unit="m/s²">CH1</container>' in result


@pytest.mark.usefixtures("xmllint_executable")
def test_core_sources_and_committed_artifacts_have_byte_parity() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "curious_signals", "check-generated"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert {path.name for path in CORE_SOURCE_DIR.glob("*.phyphox.xml")} == {
        f"{path.name}.xml" for path in CORE_ARTIFACT_DIR.glob("*.phyphox")
    }


@pytest.mark.usefixtures("xmllint_executable")
@pytest.mark.parametrize("inventory_change", ["missing", "extra", "invalid"])
def test_build_rejects_bad_source_inventory_or_content_before_writing(
    checkout_copy: Checkout, tmp_path: Path, inventory_change: str
) -> None:
    sources = checkout_copy.core_sources()
    if inventory_change == "missing":
        sources[-1].unlink()
    elif inventory_change == "extra":
        rogue = checkout_copy.core_source_dir / "rogue.phyphox.xml"
        rogue.write_text(sources[0].read_text(encoding="utf-8"), encoding="utf-8")
    else:
        sources[0].write_text(
            sources[0].read_text(encoding="utf-8").replace('version="1.7"', "", 1),
            encoding="utf-8",
        )
    destination = tmp_path / "output"

    with pytest.raises(ToolError):
        build(checkout_copy, destination)

    assert not destination.exists()


def test_build_and_validate_reject_unsafe_xml_before_invoking_xmllint(
    checkout_copy: Checkout, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = checkout_copy.core_sources()[0]
    source.write_text(
        source.read_text(encoding="utf-8").replace(
            "<phyphox", '<phyphox xml:base="https://example.invalid/"', 1
        ),
        encoding="utf-8",
    )
    calls = install_fake_xmllint(tmp_path / "bin", monkeypatch, delegate_to=None)

    with pytest.raises(ToolError, match="xml:base"):
        build(checkout_copy, tmp_path / "output")
    assert "xml:base" in "\n".join(validate(checkout_copy))
    assert not calls.exists(), f"xmllint invoked before preflight completed: {calls.read_text()}"
    assert not (tmp_path / "output").exists()


def test_build_rejects_libxml_alternate_namespace_before_invoking_xmllint(
    checkout_copy: Checkout, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = checkout_copy.core_sources()[0]
    source.write_text(
        source.read_text(encoding="utf-8").replace(
            "http://www.w3.org/2001/XInclude",
            "http://www.w3.org/2003/XInclude",
        ),
        encoding="utf-8",
    )
    calls = install_fake_xmllint(tmp_path / "bin", monkeypatch, delegate_to=None)

    with pytest.raises(ToolError, match="namespace"):
        build(checkout_copy, tmp_path / "output")

    assert not calls.exists(), f"xmllint invoked before preflight completed: {calls.read_text()}"
    assert not (tmp_path / "output").exists()


@pytest.mark.usefixtures("xmllint_executable")
def test_build_rejects_symlinked_output_without_writing_any_artifact(
    checkout_copy: Checkout, tmp_path: Path
) -> None:
    destination = tmp_path / "output"
    destination.mkdir()
    outside = tmp_path / "outside.phyphox"
    outside.write_text("unchanged", encoding="utf-8")
    output_name = checkout_copy.core_sources()[0].name.removesuffix(".xml")
    (destination / output_name).symlink_to(outside)

    with pytest.raises(ToolError, match="output must not be a symlink"):
        build(checkout_copy, destination)

    assert outside.read_text(encoding="utf-8") == "unchanged"
    assert list(destination.iterdir()) == [destination / output_name]


@pytest.mark.usefixtures("xmllint_executable")
def test_build_rejects_symlinked_destination(checkout_copy: Checkout, tmp_path: Path) -> None:
    actual_destination = tmp_path / "actual-output"
    actual_destination.mkdir()
    destination = tmp_path / "output"
    destination.symlink_to(actual_destination, target_is_directory=True)

    with pytest.raises(ToolError, match="destination must not be a symlink"):
        build(checkout_copy, destination)

    assert list(actual_destination.iterdir()) == []


@pytest.mark.usefixtures("xmllint_executable")
def test_validate_expands_each_source_once(
    checkout_copy: Checkout,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    xmllint_executable: str,
) -> None:
    calls = install_fake_xmllint(tmp_path / "bin", monkeypatch, delegate_to=xmllint_executable)

    assert validate(checkout_copy) == []
    expansions = [
        line for line in calls.read_text(encoding="utf-8").splitlines() if "--xinclude" in line
    ]
    assert len(expansions) == len(checkout_copy.core_sources()) == 7
