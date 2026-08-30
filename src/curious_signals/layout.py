"""Repository paths used by the local tooling."""

from __future__ import annotations

from pathlib import Path


def repository_root() -> Path:
    """Return the checkout root containing this source package."""

    return Path(__file__).resolve().parents[2]


def core_source_dir() -> Path:
    return repository_root() / "src" / "phyphox"


def core_include_dir() -> Path:
    return core_source_dir() / "includes"


def experiments_dir() -> Path:
    return repository_root() / "experiments"


def astronomy_dir() -> Path:
    return experiments_dir() / "astronomy"


def firmware_path() -> Path:
    return repository_root() / "arduino" / "phyphox_ble_sense" / "phyphox_ble_sense.ino"


def contract_path() -> Path:
    return repository_root() / "protocol" / "contract.json"
