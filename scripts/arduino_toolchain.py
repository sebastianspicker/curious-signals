"""Provision or verify the pinned contributor Arduino toolchain."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

MANIFEST = Path(__file__).with_name("arduino-toolchain.json")


def installed_versions(arguments: list[str]) -> dict:
    result = subprocess.run(
        ["arduino-cli", *arguments, "--format", "json"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    if not isinstance(data, dict):
        raise ValueError("Arduino CLI returned a non-object JSON response")
    return data


def verify(toolchain: dict) -> list[str]:
    """Check local installations without refreshing indexes or installing packages."""
    core_name, core_version = toolchain["core"].split("@")
    cores = installed_versions(["core", "list"]).get("platforms", [])
    errors = []
    if not any(
        core.get("id") == core_name and core.get("installed_version") == core_version
        for core in cores
    ):
        errors.append(f"Required core is not installed: {toolchain['core']}")
    libraries = installed_versions(["lib", "list"]).get("installed_libraries", [])
    for pin in toolchain["libraries"]:
        name, version = pin.split("@")
        matches = [
            entry["library"].get("version")
            for entry in libraries
            if entry.get("library", {}).get("name") == name
        ]
        if matches != [version]:
            errors.append(f"Required library is missing or ambiguous: {pin} (found {matches})")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("provision", "verify", "fqbn"))
    args = parser.parse_args()
    try:
        toolchain = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if args.action == "fqbn":
            print(toolchain["fqbn"])
            return 0
        if args.action == "provision":
            for command in (
                ["core", "update-index"],
                ["core", "install", toolchain["core"]],
                ["lib", "install", *toolchain["libraries"]],
            ):
                subprocess.run(["arduino-cli", *command], check=True)
        errors = verify(toolchain)
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f"Arduino toolchain check failed: {error}", file=sys.stderr)
        return 2
    if errors:
        print(
            "\n".join([*errors, "Run make provision to install the pinned packages."]),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
