from __future__ import annotations

import tomllib
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PYTHON_ROOT = REPOSITORY_ROOT / "src" / "python"
PROJECTKOIOS_ROOT = PYTHON_ROOT / "projectkoios"
EXPECTED_PACKAGE_INCLUDES = (
    "projectkoios.simulations",
    "projectkoios.simulations.*",
    "projectkoios.simulation_workflows",
    "projectkoios.simulation_workflows.*",
    "projectkoios.integrations",
    "projectkoios.integrations.*",
    "projectkoios.adapters",
    "projectkoios.adapters.*",
)
OWNED_NAMESPACE_PREFIXES = (
    "projectkoios.simulations",
    "projectkoios.simulation_workflows",
    "projectkoios.integrations",
    "projectkoios.adapters",
)
EXPECTED_PACKAGE_DATA = {
    "projectkoios.simulations": ["py.typed"],
    "projectkoios.simulation_workflows": ["py.typed"],
    "projectkoios.integrations": ["py.typed"],
    "projectkoios.integrations.wannier90": ["provenance.json"],
}


def _pyproject() -> dict[str, Any]:
    with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)


def test_wheel_discovery_declares_owned_namespace_directions() -> None:
    configuration = _pyproject()["tool"]["setuptools"]

    assert configuration["packages"]["find"] == {
        "where": ["src/python"],
        "include": list(EXPECTED_PACKAGE_INCLUDES),
        "namespaces": True,
    }
    assert configuration["package-data"] == EXPECTED_PACKAGE_DATA


def test_current_wheel_packages_are_limited_to_owned_namespace_directions() -> None:
    package_names = {
        ".".join(path.parent.relative_to(PYTHON_ROOT).parts)
        for path in PROJECTKOIOS_ROOT.rglob("*.py")
    }

    assert package_names
    assert all(
        package_name.startswith(OWNED_NAMESPACE_PREFIXES)
        for package_name in package_names
    )
    assert all(
        any(
            fnmatchcase(package_name, include_pattern)
            for include_pattern in EXPECTED_PACKAGE_INCLUDES
        )
        for package_name in package_names
    )
