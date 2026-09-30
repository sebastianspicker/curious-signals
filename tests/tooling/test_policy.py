from __future__ import annotations

import tomllib

import pytest

from tests.conftest import REPO_ROOT

PROJECT = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def is_constrained(requirements: list[str], package: str) -> bool:
    return any(
        item.startswith(package) and any(operator in item for operator in "<>=~!")
        for item in requirements
    )


def test_python_floor_is_3_11() -> None:
    assert PROJECT["requires-python"] == ">=3.11"


def test_runtime_dependency_is_version_constrained() -> None:
    assert is_constrained(PROJECT["dependencies"], "defusedxml")


@pytest.mark.parametrize(
    ("extra", "package"), [("test", "pytest"), ("test", "ruff"), ("browser", "playwright")]
)
def test_optional_dependencies_are_version_constrained(extra: str, package: str) -> None:
    assert is_constrained(PROJECT["optional-dependencies"][extra], package)
