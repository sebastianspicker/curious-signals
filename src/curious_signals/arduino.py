"""Provision, verify, and compile with the pinned contributor Arduino toolchain.

This module uses only the standard library so firmware compilation never needs the
XML tooling dependencies.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import ToolError


@dataclass(frozen=True)
class Toolchain:
    """The pinned Arduino target parsed from the toolchain manifest."""

    fqbn: str
    core: tuple[str, str]
    libraries: tuple[tuple[str, str], ...]


def _pin(value: object, label: str) -> tuple[str, str]:
    parts = value.split("@") if isinstance(value, str) else []
    if len(parts) != 2 or not all(parts):
        raise ToolError(f"{label} must be a name@version pin: {value!r}")
    return parts[0], parts[1]


def _format_pin(pin: tuple[str, str]) -> str:
    return "@".join(pin)


def load_toolchain(path: Path) -> Toolchain:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ToolError(f"Arduino toolchain manifest is unreadable: {error}") from error
    if not isinstance(manifest, dict):
        raise ToolError("Arduino toolchain manifest must be a JSON object")
    fqbn = manifest.get("fqbn")
    if not isinstance(fqbn, str) or not fqbn:
        raise ToolError("Arduino toolchain manifest: fqbn must be a non-empty string")
    core = _pin(manifest.get("core"), "Arduino toolchain manifest: core")
    libraries = manifest.get("libraries")
    if not isinstance(libraries, list):
        raise ToolError("Arduino toolchain manifest: libraries must be a list")
    return Toolchain(
        fqbn=fqbn,
        core=core,
        libraries=tuple(
            _pin(library, "Arduino toolchain manifest: library") for library in libraries
        ),
    )


def _run(arguments: list[str], *, capture: bool = False) -> str:
    try:
        result = subprocess.run(
            ["arduino-cli", *arguments],
            capture_output=capture,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise ToolError(f"arduino-cli {' '.join(arguments)} failed: {error}") from error
    return result.stdout if capture else ""


def _installed(arguments: list[str], key: str) -> list[dict]:
    """Return the list of objects under ``key`` in an arduino-cli JSON response."""

    try:
        data = json.loads(_run([*arguments, "--format", "json"], capture=True))
    except ValueError as error:
        raise ToolError(f"Arduino CLI returned invalid JSON: {error}") from error
    if not isinstance(data, dict):
        raise ToolError("Arduino CLI returned a non-object JSON response")
    entries = data.get(key, [])
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise ToolError(
            f"Arduino CLI returned an unexpected response: {key} must be a list of objects"
        )
    return entries


def _library_objects(entries: list[dict]) -> list[dict]:
    libraries = [entry.get("library", {}) for entry in entries]
    if not all(isinstance(library, dict) for library in libraries):
        raise ToolError(
            "Arduino CLI returned an unexpected response: "
            "installed_libraries entries must contain a library object"
        )
    return libraries


def verify(toolchain: Path) -> list[str]:
    """Check local installations without refreshing indexes or installing packages."""
    manifest = load_toolchain(toolchain)
    core_name, core_version = manifest.core
    errors = []
    if not any(
        core.get("id") == core_name and core.get("installed_version") == core_version
        for core in _installed(["core", "list"], "platforms")
    ):
        errors.append(f"Required core is not installed: {_format_pin(manifest.core)}")
    libraries = _library_objects(_installed(["lib", "list"], "installed_libraries"))
    for pin in manifest.libraries:
        matches = [library.get("version") for library in libraries if library.get("name") == pin[0]]
        if matches != [pin[1]]:
            errors.append(
                f"Required library is missing or ambiguous: {_format_pin(pin)} (found {matches})"
            )
    return errors


def _verified(toolchain: Path) -> None:
    errors = verify(toolchain)
    if errors:
        raise ToolError("\n".join([*errors, "Run make provision to install the pinned packages."]))


def provision(toolchain: Path) -> None:
    manifest = load_toolchain(toolchain)
    for command in (
        ["core", "update-index"],
        ["core", "install", _format_pin(manifest.core)],
        ["lib", "install", *(_format_pin(pin) for pin in manifest.libraries)],
    ):
        _run(command)
    _verified(toolchain)


def compile_sketch(toolchain: Path, sketch_dir: Path) -> None:
    manifest = load_toolchain(toolchain)
    if shutil.which("arduino-cli") is None:
        raise ToolError("arduino-cli not found. Install it first (see README.md).")
    _verified(toolchain)
    _run(["compile", "--fqbn", manifest.fqbn, str(sketch_dir)])
