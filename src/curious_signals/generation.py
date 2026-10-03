"""XInclude expansion, generated-artifact parity, and deterministic bundling."""

from __future__ import annotations

import os
import tempfile
import zipfile
from collections.abc import Iterable
from pathlib import Path

from . import ToolError
from .checkout import Checkout
from .phyphox_xml import check_core_experiment
from .protocol import Protocol, load_protocol
from .xinclude import validate_xinclude_paths
from .xmllint import expand_xincludes, find_xmllint

BUNDLE_DATE_TIME = (1980, 1, 1, 0, 0, 0)


def source_inventory_errors(checkout: Checkout, protocol: Protocol) -> list[str]:
    sources = checkout.core_sources()
    if not sources:
        return [f"No source files found at {checkout.core_source_dir}/*.phyphox.xml."]
    expected = set(protocol.experiments)
    actual = {source.name.removesuffix(".xml") for source in sources}
    if actual != expected:
        return [
            f"{checkout.core_source_dir}: source inventory does not match protocol contract "
            f"(missing={sorted(expected - actual)}, extra={sorted(actual - expected)})"
        ]
    return []


def xml_safety_errors(paths: Iterable[Path], include_root: Path) -> list[str]:
    return [
        error
        for path in paths
        for error in validate_xinclude_paths(path, allowed_root=include_root)
    ]


def render_core_experiments(checkout: Checkout, protocol: Protocol) -> list[tuple[str, str]]:
    """Validate every core input and render all outputs before any destination write."""

    sources = checkout.core_sources()
    errors = source_inventory_errors(checkout, protocol)
    errors.extend(xml_safety_errors([*sources, *checkout.includes()], checkout.include_dir))
    if errors:
        raise ToolError("\n".join(errors))
    xmllint = find_xmllint()
    rendered = [
        (source.name.removesuffix(".xml"), expand_xincludes(source, xmllint)) for source in sources
    ]
    with tempfile.TemporaryDirectory(prefix="curious-signals-prewrite-") as temporary:
        temporary_dir = Path(temporary)
        for name, content in rendered:
            candidate = temporary_dir / name
            candidate.write_text(content, encoding="utf-8")
            errors.extend(
                check_core_experiment(candidate, protocol, expected_mode=protocol.mode_id_for(name))
            )
    if errors:
        raise ToolError("\n".join(errors))
    return rendered


def _atomic_write_text(output: Path, content: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        dir=output.parent, prefix=f".{output.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
        temporary.chmod(0o644)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def _write(rendered: list[tuple[str, str]], destination: Path) -> list[Path]:
    if destination.is_symlink():
        raise ToolError(f"{destination}: generated experiment destination must not be a symlink")
    try:
        destination.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise ToolError(f"{destination}: cannot write generated experiments: {error}") from error
    outputs = [destination / name for name, _content in rendered]
    if symlink := next((output for output in outputs if output.is_symlink()), None):
        raise ToolError(f"{symlink}: generated experiment output must not be a symlink")
    try:
        for output, (_name, content) in zip(outputs, rendered, strict=True):
            _atomic_write_text(output, content)
    except OSError as error:
        raise ToolError(f"{destination}: cannot write generated experiments: {error}") from error
    return outputs


def build(checkout: Checkout, output_dir: Path | None = None) -> list[Path]:
    """Expand safe XIncludes into the generated core experiment directory."""

    rendered = render_core_experiments(checkout, load_protocol(checkout.contract))
    return _write(rendered, output_dir or checkout.experiments_dir)


def check_generated(checkout: Checkout) -> list[str]:
    """Return generated-artifact parity errors without changing repository files."""

    rendered = render_core_experiments(checkout, load_protocol(checkout.contract))
    with tempfile.TemporaryDirectory(prefix="curious-signals-generated-") as temporary:
        built = _write(rendered, Path(temporary))
        generated = checkout.generated_experiments()
        if len(built) != len(generated):
            return ["Generated experiments are not up to date."]
        errors: list[str] = []
        for generated_file in generated:
            candidate = Path(temporary) / generated_file.name
            if not candidate.is_file() or candidate.read_bytes() != generated_file.read_bytes():
                errors.append(f"Out-of-date generated artifact: {generated_file.name}")
        return errors


def bundle(checkout: Checkout, output_path: Path) -> Path:
    """Build in isolation and write a byte-stable ZIP without changing tracked artifacts."""

    rendered = render_core_experiments(checkout, load_protocol(checkout.contract))
    with tempfile.TemporaryDirectory(prefix="curious-signals-bundle-") as temporary:
        files = _write(rendered, Path(temporary))
        try:
            with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(files, key=lambda candidate: candidate.name):
                    entry = zipfile.ZipInfo(path.name, date_time=BUNDLE_DATE_TIME)
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    entry.external_attr = 0o100644 << 16
                    archive.writestr(entry, path.read_bytes())
        except OSError as error:
            raise ToolError(f"{output_path}: cannot write bundle: {error}") from error
    return output_path
