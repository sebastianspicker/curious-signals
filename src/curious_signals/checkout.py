"""Paths inside one repository checkout used by the local tooling."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Checkout:
    """One repository checkout; every tooling path derives from its root."""

    root: Path

    @classmethod
    def default(cls) -> Checkout:
        """Return the checkout containing this source package.

        This assumes a source checkout (``PYTHONPATH=src`` or an editable install); an
        installed copy in site-packages has no repository root above it.
        """

        return cls(Path(__file__).resolve().parents[2])

    @property
    def contract(self) -> Path:
        return self.root / "protocol" / "contract.json"

    @property
    def core_source_dir(self) -> Path:
        return self.root / "src" / "phyphox"

    @property
    def include_dir(self) -> Path:
        return self.core_source_dir / "includes"

    @property
    def experiments_dir(self) -> Path:
        return self.root / "experiments"

    @property
    def astronomy_dir(self) -> Path:
        return self.experiments_dir / "astronomy"

    @property
    def sketch_dir(self) -> Path:
        return self.root / "arduino" / "phyphox_ble_sense"

    @property
    def arduino_toolchain(self) -> Path:
        return self.root / "arduino" / "toolchain.json"

    def core_sources(self) -> list[Path]:
        return sorted(self.core_source_dir.glob("*.phyphox.xml"))

    def includes(self) -> list[Path]:
        return sorted(self.include_dir.glob("*.xml"))

    def generated_experiments(self) -> list[Path]:
        return sorted(self.experiments_dir.glob("*.phyphox"))

    def astronomy_experiments(self) -> list[Path]:
        return sorted(self.astronomy_dir.glob("*.phyphox"))
