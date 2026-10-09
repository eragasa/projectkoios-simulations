from __future__ import annotations

import ast
import sys
from pathlib import Path

PROJECTKOIOS_ROOT = (
    Path(__file__).resolve().parents[2] / "src" / "python" / "projectkoios"
)
SOURCE_ROOT = PROJECTKOIOS_ROOT / "simulations"
SIMULATION_WORKFLOWS_ROOT = SOURCE_ROOT / "workflows"


def _projectkoios_imports(path: Path) -> tuple[str, ...]:
    names: list[str] = []
    for node in ast.walk(
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    ):
        if isinstance(node, ast.Import):
            names.extend(
                alias.name for alias in node.names if alias.name == "projectkoios"
            )
            names.extend(
                alias.name
                for alias in node.names
                if alias.name.startswith("projectkoios.")
            )
        elif isinstance(node, ast.ImportFrom):
            imported_name = _resolve_import_from(path, node)
            if imported_name == "projectkoios" or imported_name.startswith(
                "projectkoios."
            ):
                names.append(imported_name)
    return tuple(names)


def _resolve_import_from(path: Path, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    relative_module = path.relative_to(SOURCE_ROOT).with_suffix("")
    package_parts = (
        "projectkoios",
        "simulations",
        *relative_module.parts[:-1],
    )
    if node.level > len(package_parts):
        return "projectkoios.outside-neutral-namespace"
    resolved_parts = package_parts[: len(package_parts) - node.level + 1]
    if node.module is not None:
        resolved_parts += tuple(node.module.split("."))
    return ".".join(resolved_parts)


def _absolute_imports(path: Path) -> tuple[str, ...]:
    names: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            names.append(node.module or "")
    return tuple(names)


def test_relative_provider_imports_resolve_outside_the_neutral_namespace() -> None:
    parsed = ast.parse("from .....integrations import quantum_espresso")
    node = parsed.body[0]
    assert isinstance(node, ast.ImportFrom)
    path = SOURCE_ROOT / "dft" / "pw" / "scf" / "example.py"

    assert _resolve_import_from(path, node) == "projectkoios.integrations"


def test_protected_simulations_core_cannot_import_workflows_or_outward_code() -> None:
    invalid: list[tuple[Path, str]] = []
    allowed_roots = (
        "projectkoios.physkit",
        "projectkoios.simulations",
    )
    workflow_namespace = "projectkoios.simulations.workflows"

    for path in SOURCE_ROOT.rglob("*.py"):
        if SIMULATION_WORKFLOWS_ROOT in path.parents:
            continue
        for imported_name in _projectkoios_imports(path):
            is_allowed = any(
                imported_name == root or imported_name.startswith(f"{root}.")
                for root in allowed_roots
            )
            imports_workflows = imported_name == workflow_namespace or (
                imported_name.startswith(f"{workflow_namespace}.")
            )
            if not is_allowed or imports_workflows:
                invalid.append((path.relative_to(SOURCE_ROOT), imported_name))

    assert invalid == []


def test_simulation_workflows_import_only_standard_library_and_core() -> None:
    invalid: list[tuple[Path, str]] = []
    allowed_project_roots = (
        "projectkoios.simulations",
        "projectkoios.simulations.workflows",
    )

    for path in SIMULATION_WORKFLOWS_ROOT.rglob("*.py"):
        for imported_name in _absolute_imports(path):
            if not imported_name:
                continue
            if imported_name == "projectkoios" or imported_name.startswith(
                "projectkoios."
            ):
                if not any(
                    imported_name == root or imported_name.startswith(f"{root}.")
                    for root in allowed_project_roots
                ):
                    invalid.append(
                        (path.relative_to(SIMULATION_WORKFLOWS_ROOT), imported_name)
                    )
                continue
            import_root = imported_name.split(".", 1)[0]
            is_local_cpn = (
                SIMULATION_WORKFLOWS_ROOT / "pw_dft_scf" / "cpn"
            ) in path.parents
            if import_root == "snakes" and is_local_cpn:
                continue
            if import_root not in sys.stdlib_module_names:
                invalid.append(
                    (path.relative_to(SIMULATION_WORKFLOWS_ROOT), imported_name)
                )

    assert invalid == []
