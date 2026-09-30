"""Provision, verify, and compile with the pinned contributor Arduino toolchain.

This module uses only the standard library so firmware compilation never needs the
XML tooling dependencies.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import ToolError


def _pin(value: object, label: str) -> tuple[str, str]:
    parts = value.split("@") if isinstance(value, str) else []
    if len(parts) != 2 or not all(parts):
        raise ToolError(f"{label} must be a name@version pin: {value!r}")
    return parts[0], parts[1]


def load_toolchain(path: Path) -> dict:
    try:
        toolchain = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ToolError(f"Arduino toolchain manifest is unreadable: {error}") from error
    if not isinstance(toolchain, dict):
        raise ToolError("Arduino toolchain manifest must be a JSON object")
    if not isinstance(toolchain.get("fqbn"), str) or not toolchain["fqbn"]:
        raise ToolError("Arduino toolchain manifest: fqbn must be a non-empty string")
    _pin(toolchain.get("core"), "Arduino toolchain manifest: core")
    libraries = toolchain.get("libraries")
    if not isinstance(libraries, list):
        raise ToolError("Arduino toolchain manifest: libraries must be a list")
    for library in libraries:
        _pin(library, "Arduino toolchain manifest: library")
    return toolchain


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


def _installed(arguments: list[str]) -> dict:
    try:
        data = json.loads(_run([*arguments, "--format", "json"], capture=True))
    except ValueError as error:
        raise ToolError(f"Arduino CLI returned invalid JSON: {error}") from error
    if not isinstance(data, dict):
        raise ToolError("Arduino CLI returned a non-object JSON response")
    return data


def verify(toolchain: Path) -> list[str]:
    """Check local installations without refreshing indexes or installing packages."""
    manifest = load_toolchain(toolchain)
    core_name, core_version = _pin(manifest["core"], "core")
    cores = _installed(["core", "list"]).get("platforms", [])
    errors = []
    if not any(
        core.get("id") == core_name and core.get("installed_version") == core_version
        for core in cores
    ):
        errors.append(f"Required core is not installed: {manifest['core']}")
    libraries = _installed(["lib", "list"]).get("installed_libraries", [])
    for pin in manifest["libraries"]:
        name, version = _pin(pin, "library")
        matches = [
            entry["library"].get("version")
            for entry in libraries
            if entry.get("library", {}).get("name") == name
        ]
        if matches != [version]:
            errors.append(f"Required library is missing or ambiguous: {pin} (found {matches})")
    return errors


def _verified(toolchain: Path) -> None:
    try:
        errors = verify(toolchain)
    except (AttributeError, KeyError, TypeError) as error:
        raise ToolError(f"Arduino CLI returned an unexpected response: {error!r}") from error
    if errors:
        raise ToolError("\n".join([*errors, "Run make provision to install the pinned packages."]))


def provision(toolchain: Path) -> None:
    manifest = load_toolchain(toolchain)
    for command in (
        ["core", "update-index"],
        ["core", "install", manifest["core"]],
        ["lib", "install", *manifest["libraries"]],
    ):
        _run(command)
    _verified(toolchain)


def compile_sketch(toolchain: Path, sketch_dir: Path) -> None:
    manifest = load_toolchain(toolchain)
    if shutil.which("arduino-cli") is None:
        raise ToolError("arduino-cli not found. Install it first (see README.md).")
    _verified(toolchain)
    _run(["compile", "--fqbn", manifest["fqbn"], str(sketch_dir)])
