from __future__ import annotations

import ast
from pathlib import Path

SOURCE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "python"
    / "projectkoios"
    / "simulations"
)


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
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            if node.module == "projectkoios" or node.module.startswith("projectkoios."):
                names.append(node.module)
    return tuple(names)


def test_simulations_depend_only_on_the_simulations_namespace() -> None:
    invalid: list[tuple[Path, str]] = []

    for path in SOURCE_ROOT.rglob("*.py"):
        for imported_name in _projectkoios_imports(path):
            if not (
                imported_name == "projectkoios.simulations"
                or imported_name.startswith("projectkoios.simulations.")
            ):
                invalid.append((path.relative_to(SOURCE_ROOT), imported_name))

    assert invalid == []
