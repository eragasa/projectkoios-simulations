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


def test_relative_provider_imports_resolve_outside_the_neutral_namespace() -> None:
    parsed = ast.parse("from .....integrations import quantum_espresso")
    node = parsed.body[0]
    assert isinstance(node, ast.ImportFrom)
    path = SOURCE_ROOT / "dft" / "pw" / "scf" / "example.py"

    assert _resolve_import_from(path, node) == "projectkoios.integrations"


def test_neutral_simulations_do_not_import_outward_namespaces() -> None:
    invalid: list[tuple[Path, str]] = []

    for path in SOURCE_ROOT.rglob("*.py"):
        for imported_name in _projectkoios_imports(path):
            if not (
                imported_name == "projectkoios.simulations"
                or imported_name.startswith("projectkoios.simulations.")
            ):
                invalid.append((path.relative_to(SOURCE_ROOT), imported_name))

    assert invalid == []
