"""Build, validation, parity, and archive workflows for repository assets."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

from .contract import active_modes, load_contract, validate_contract
from .layout import astronomy_dir, core_include_dir, core_source_dir, experiments_dir
from .postprocess import postprocess
from .repository_contracts import validate_repository_contract
from .xinclude import validate_xinclude_paths
from .xml_contracts import validate_phyphox


class ToolError(RuntimeError):
    """An unavailable or failing required external XML utility."""


def _core_sources() -> list[Path]:
    return sorted(core_source_dir().glob("*.phyphox.xml"))


def _core_includes() -> list[Path]:
    return sorted(core_include_dir().glob("*.xml"))


def _generated_files() -> list[Path]:
    return sorted(experiments_dir().glob("*.phyphox"))


def _astronomy_files() -> list[Path]:
    return sorted(astronomy_dir().glob("*.phyphox"))


def _require_xmllint() -> str:
    executable = shutil.which("xmllint")
    if executable is None:
        raise ToolError("xmllint not found. Install libxml2 utilities first.")
    return executable


def _run_xmllint(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(arguments, check=False, capture_output=True, text=True)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "xmllint failed"
        raise ToolError(detail)
    return result


def _expanded_xml(source: Path, xmllint: str) -> str:
    return postprocess(_run_xmllint([xmllint, "--xinclude", str(source)]).stdout)


def _validate_source_inventory(sources: list[Path], contract: dict[str, object]) -> list[str]:
    if not sources:
        return [f"No source files found at {core_source_dir()}/*.phyphox.xml."]
    expected = {mode["experiment"] for mode in active_modes(contract)}
    actual = {source.name.removesuffix(".xml") for source in sources}
    if actual != expected:
        return [
            f"{core_source_dir()}: source inventory does not match protocol contract "
            f"(missing={sorted(expected - actual)}, extra={sorted(actual - expected)})"
        ]
    return []


def _render_core_sources() -> list[tuple[str, str]]:
    """Validate every core input and render all outputs before any destination write."""

    try:
        contract = load_contract()
    except ValueError as error:
        raise ToolError(str(error)) from error
    errors = validate_contract(contract)
    sources = _core_sources()
    errors.extend(_validate_source_inventory(sources, contract))
    if not errors:
        errors.extend(validate_repository_contract(contract))
    include_errors = [
        error for path in [*sources, *_core_includes()] for error in validate_xinclude_paths(path)
    ]
    errors.extend(include_errors)
    if errors:
        raise ToolError("\n".join(errors))
    xmllint = _require_xmllint()
    rendered = [
        (source.name.removesuffix(".xml"), _expanded_xml(source, xmllint)) for source in sources
    ]
    bluetooth = contract["bluetooth"]
    frame = contract["frame"]
    with tempfile.TemporaryDirectory(prefix="curious-signals-prewrite-") as temporary:
        temporary_dir = Path(temporary)
        for name, content in rendered:
            candidate = temporary_dir / name
            candidate.write_text(content, encoding="utf-8")
            errors.extend(
                error.message
                for error in validate_phyphox(
                    candidate,
                    bluetooth["data_char_uuid"],
                    bluetooth["config_char_uuid"],
                    {field["offset"] for field in frame["data"]["fields"]},
                    frame["data"]["encoding"],
                    frame["config"]["encoding"],
                )
            )
    if errors:
        raise ToolError("\n".join(errors))
    return rendered


def build(output_dir: Path | None = None) -> list[Path]:
    """Expand safe XIncludes into the generated core experiment directory."""

    rendered = _render_core_sources()
    destination = output_dir or experiments_dir()
    destination.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for name, content in rendered:
        output = destination / name
        output.write_text(content, encoding="utf-8")
        outputs.append(output)
    return outputs


def check_generated() -> list[str]:
    """Return generated-artifact parity errors without changing repository files."""

    with tempfile.TemporaryDirectory(prefix="curious-signals-generated-") as temporary:
        built = build(Path(temporary))
        generated = _generated_files()
        if len(built) != len(generated):
            return ["Generated experiments are not up to date."]
        errors: list[str] = []
        for generated_file in generated:
            candidate = Path(temporary) / generated_file.name
            if not candidate.is_file() or candidate.read_bytes() != generated_file.read_bytes():
                errors.append(f"Out-of-date generated artifact: {generated_file.name}")
        return errors or []


def _syntax_errors(paths: Iterable[Path], xmllint: str) -> list[str]:
    errors: list[str] = []
    for path in paths:
        try:
            _run_xmllint([xmllint, "--noout", str(path)])
        except ToolError as error:
            errors.append(str(error))
    return errors


def validate_astronomy(paths: Iterable[Path] | None = None) -> list[str]:
    """Validate astronomy XML safety and its required English, German, French locales."""

    errors: list[str] = []
    for path in paths if paths is not None else _astronomy_files():
        try:
            root = ET.parse(path).getroot()
        except OSError as error:
            errors.append(f"{path}: cannot read XML: {error}")
            continue
        except DefusedXmlException as error:
            errors.append(f"{path}: unsafe XML rejected: {error}")
            continue
        except ET.ParseError as error:
            errors.append(f"{path}: XML parse error: {error}")
            continue
        if root.tag.split("}", 1)[-1] != "phyphox":
            errors.append(f"{path}: root element must be <phyphox>")
        if root.attrib.get("locale") != "en":
            errors.append(f"{path}: root locale must be en")
        locales = {
            element.attrib.get("locale") for element in root.findall("./translations/translation")
        }
        missing = {"de", "fr"} - locales
        if missing:
            errors.append(f"{path}: missing translation locale(s): {', '.join(sorted(missing))}")
    return errors


def validate() -> list[str]:
    """Run the complete local XML, contract, core, and astronomy validation suite."""

    errors: list[str] = []
    try:
        contract = load_contract()
    except ValueError as error:
        return [str(error)]
    errors.extend(validate_contract(contract))
    if errors:
        return errors
    try:
        xmllint = _require_xmllint()
    except ToolError as error:
        return [str(error)]
    sources = _core_sources()
    includes = _core_includes()
    generated = _generated_files()
    astronomy = _astronomy_files()
    errors.extend(_validate_source_inventory(sources, contract))
    if not generated:
        errors.append(f"No generated experiments found at {experiments_dir()}/*.phyphox.")
    expected_names = {mode["experiment"] for mode in active_modes(contract)}
    if {path.name for path in generated} != expected_names:
        errors.append(f"{experiments_dir()}: generated filenames do not match protocol contract")
    errors.extend(_syntax_errors([*includes, *sources, *generated, *astronomy], xmllint))
    for source in sources:
        errors.extend(validate_xinclude_paths(source))
        try:
            _run_xmllint([xmllint, "--xinclude", "--noout", str(source)])
        except ToolError as error:
            errors.append(str(error))
    errors.extend(validate_repository_contract(contract))
    bluetooth = contract["bluetooth"]
    for path in generated:
        errors.extend(
            error.message
            for error in validate_phyphox(
                path, bluetooth["data_char_uuid"], bluetooth["config_char_uuid"]
            )
        )
    with tempfile.TemporaryDirectory(prefix="curious-signals-validate-") as temporary:
        temporary_dir = Path(temporary)
        for source in sources:
            expanded = temporary_dir / source.name.removesuffix(".xml")
            try:
                expanded.write_text(_expanded_xml(source, xmllint), encoding="utf-8")
            except ToolError as error:
                errors.append(str(error))
                continue
            errors.extend(
                error.message
                for error in validate_phyphox(
                    expanded, bluetooth["data_char_uuid"], bluetooth["config_char_uuid"]
                )
            )
    errors.extend(validate_astronomy(astronomy))
    return errors


def bundle(output_path: Path | None = None) -> Path:
    """Build in isolation and write a byte-stable ZIP without changing tracked artifacts."""

    destination = output_path or Path("phyphox-experiments.zip")
    with tempfile.TemporaryDirectory(prefix="curious-signals-bundle-") as temporary:
        files = build(Path(temporary))
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(files, key=lambda candidate: candidate.name):
                entry = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, path.read_bytes())
    return destination
