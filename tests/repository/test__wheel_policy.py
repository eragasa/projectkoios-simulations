from __future__ import annotations

import importlib.util
import re
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
    "projectkoios.integrations",
    "projectkoios.integrations.*",
    "projectkoios.adapters",
    "projectkoios.adapters.*",
)
OWNED_NAMESPACE_PREFIXES = (
    "projectkoios.simulations",
    "projectkoios.integrations",
    "projectkoios.adapters",
)
EXPECTED_PACKAGE_DATA = {
    "projectkoios.simulations": ["py.typed"],
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


def test_optional_cpn_and_visualization_dependencies_are_not_core_runtime() -> None:
    project = _pyproject()["project"]
    snakes = (
        "SNAKES @ git+https://github.com/eragasa/projectkoios-snakes.git@"
        "72dbb1dbf0a91349faca21ceb660923cc442a8e9"
    )
    plotly = "plotly>=6.5,<7"

    assert snakes not in project["dependencies"]
    assert plotly not in project["dependencies"]
    assert project["optional-dependencies"]["cpn"] == [snakes]
    assert project["optional-dependencies"]["visualization"] == [plotly]
    assert snakes in project["optional-dependencies"]["development"]
    assert plotly in project["optional-dependencies"]["development"]


def test_replay_overlay_has_one_exclusive_package_shape() -> None:
    workflow_root = PROJECTKOIOS_ROOT / "simulations" / "workflows" / "pw_dft_scf"
    replay_root = workflow_root / "convergence" / "replay"
    expected_modules = {
        "__init__.py",
        "action.py",
        "error.py",
        "evidence.py",
        "identity.py",
        "request.py",
        "result.py",
    }

    assert {path.name for path in replay_root.glob("*.py")} == expected_modules
    assert not (workflow_root / "replay.py").exists()
    assert not (
        REPOSITORY_ROOT / "tests/projectkoios/simulations/workflows/pw_dft_scf/replay/"
        "test__PwDftScfConvergenceReplayer.py"
    ).exists()
    assert (
        REPOSITORY_ROOT / "tests/projectkoios/simulations/workflows/pw_dft_scf/replay/"
        "test__PwDftScfConvergenceReplayActionizer.py"
    ).is_file()
    assert not (
        REPOSITORY_ROOT
        / "docs/architecture/projectkoios/simulations/workflows/pw_dft_scf/"
        "replay/index.md"
    ).exists()
    assert (
        REPOSITORY_ROOT
        / "docs/architecture/projectkoios/simulations/workflows/pw_dft_scf/"
        "convergence/replay/index.md"
    ).is_file()

    source_text = "\n".join(
        path.read_text(encoding="utf-8") for path in workflow_root.rglob("*.py")
    )
    assert "PwDftScfConvergenceReplayer" not in source_text
    assert "projectkoios.simulation_workflows" not in source_text
    assert "projectkoios.applications.pw-dft-scf.convergence-replay" in source_text


def test_historical_sibling_namespace_is_absent() -> None:
    assert not (PROJECTKOIOS_ROOT / "simulation_workflows").exists()
    assert not (REPOSITORY_ROOT / "tests/projectkoios/simulation_workflows").exists()
    assert not (
        REPOSITORY_ROOT / "docs/architecture/projectkoios/simulation_workflows"
    ).exists()
    assert not (
        REPOSITORY_ROOT / "examples/projectkoios/applications/pw_dft_scf"
    ).exists()
    assert not (
        REPOSITORY_ROOT / "examples/projectkoios/applications/pw_dft_relaxation"
    ).exists()
    assert not (
        REPOSITORY_ROOT / "tests/examples/projectkoios/applications/pw_dft_scf"
    ).exists()
    assert not (
        REPOSITORY_ROOT / "tests/examples/projectkoios/applications/pw_dft_relaxation"
    ).exists()
    assert not (
        REPOSITORY_ROOT / "examples/projectkoios/simulations/workflows"
    ).exists()
    assert not (
        REPOSITORY_ROOT / "tests/examples/projectkoios/simulations/workflows"
    ).exists()
    assert (REPOSITORY_ROOT / "examples/workflows/pw_dft_scf/campaigns").is_dir()
    assert (REPOSITORY_ROOT / "tools/pw_dft_scf").is_dir()


def test_nested_workflow_imports_resolve_without_an_old_path_facade() -> None:
    assert importlib.util.find_spec("projectkoios.simulations.workflows") is not None
    assert (
        importlib.util.find_spec(
            "projectkoios.simulations.workflows.pw_dft_scf.convergence.replay"
        )
        is not None
    )
    assert importlib.util.find_spec("projectkoios.simulation_workflows") is None


def test_workflow_architecture_nodes_have_complete_substantive_trios() -> None:
    documentation_root = (
        REPOSITORY_ROOT / "docs/architecture/projectkoios/simulations/workflows"
    )
    nodes = tuple(path.parent for path in documentation_root.rglob("index.md"))

    assert len(nodes) == 58
    for node in nodes:
        for filename in ("index.md", "schematics.md", "implementation.md"):
            document = node / filename
            assert document.is_file(), document
            assert len(document.read_text(encoding="utf-8").strip()) >= 100, document


def test_workflow_architecture_local_links_resolve() -> None:
    documentation_root = (
        REPOSITORY_ROOT / "docs/architecture/projectkoios/simulations/workflows"
    )
    invalid: list[tuple[Path, str]] = []
    for document in documentation_root.rglob("*.md"):
        for target in re.findall(
            r"\[[^\]]*\]\(([^)]+)\)",
            document.read_text(encoding="utf-8"),
        ):
            local_target = target.split("#", 1)[0]
            if not local_target or "://" in local_target:
                continue
            if not (document.parent / local_target).resolve().exists():
                invalid.append((document.relative_to(REPOSITORY_ROOT), target))

    assert invalid == []
