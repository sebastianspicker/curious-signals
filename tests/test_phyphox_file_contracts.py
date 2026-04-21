"""Repository-level contract tests for phyphox experiments."""

from __future__ import annotations

from pathlib import Path

import pytest
from validate_phyphox import _load_expected_uuids, validate_phyphox

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPO_ROOT / "src" / "phyphox"
EXPERIMENTS_DIR = REPO_ROOT / "experiments"


@pytest.fixture(scope="module")
def expected_uuids() -> tuple[str | None, str | None, str | None]:
    service_uuid, data_uuid, config_uuid, errors = _load_expected_uuids()
    assert errors == []
    assert service_uuid is not None
    assert data_uuid is not None
    assert config_uuid is not None
    return service_uuid, data_uuid, config_uuid


def _source_files() -> list[Path]:
    return sorted(SOURCE_DIR.glob("*.phyphox.xml"))


def _generated_files() -> list[Path]:
    return sorted(EXPERIMENTS_DIR.glob("*.phyphox"))


def _root_locale(path: Path) -> str:
    import xml.etree.ElementTree as ET

    return ET.parse(path).getroot().attrib.get("locale", "")


def _translation_locales(path: Path) -> set[str]:
    import xml.etree.ElementTree as ET

    root = ET.parse(path).getroot()
    locales: set[str] = set()
    for translation in root.findall("./translations/translation"):
        locale = translation.attrib.get("locale")
        if locale:
            locales.add(locale)
    return locales


def test_expected_file_inventory() -> None:
    source_files = _source_files()
    generated_files = _generated_files()

    assert len(source_files) == 7
    assert len(generated_files) == 7
    assert [path.name.replace(".phyphox.xml", "") for path in source_files] == [
        path.name.replace(".phyphox", "") for path in generated_files
    ]


@pytest.mark.parametrize("path", _source_files(), ids=lambda path: path.name)
def test_source_files_have_supported_locales(path: Path) -> None:
    assert _root_locale(path) == "en"
    assert {"de", "fr"}.issubset(_translation_locales(path))


@pytest.mark.parametrize("path", _source_files(), ids=lambda path: path.name)
def test_source_files_reference_shared_includes(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert 'href="includes/containers_ch0_ch5.xml"' in text
    assert 'href="includes/bluetooth_outputs_ch1_ch5.xml"' in text


@pytest.mark.parametrize("path", _generated_files(), ids=lambda path: path.name)
def test_generated_files_validate(
    path: Path, expected_uuids: tuple[str | None, str | None, str | None]
) -> None:
    _, data_uuid, config_uuid = expected_uuids
    errors = validate_phyphox(str(path), data_uuid, config_uuid)
    assert errors == []
