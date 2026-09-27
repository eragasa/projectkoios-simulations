from __future__ import annotations

import ast
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src" / "python" / "projectkoios"
SIMULATIONS_ROOT = SOURCE_ROOT / "simulations"
INTEGRATIONS_ROOT = SOURCE_ROOT / "integrations"


def _absolute_imports(path: Path) -> tuple[str, ...]:
    imports: list[str] = []
    for node in ast.walk(
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    ):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            imports.append(node.module or "")
    return tuple(imports)


def test_neutral_simulations_never_import_outward_integrations() -> None:
    invalid = [
        path.relative_to(SIMULATIONS_ROOT)
        for path in SIMULATIONS_ROOT.rglob("*.py")
        if any(
            name == "projectkoios.integrations"
            or name.startswith("projectkoios.integrations.")
            for name in _absolute_imports(path)
        )
    ]

    assert invalid == []


def test_integrations_have_no_donor_or_execution_dependencies() -> None:
    forbidden_roots = {"ksdft2effmass", "subprocess", "socket"}
    invalid: list[tuple[Path, str]] = []

    for path in INTEGRATIONS_ROOT.rglob("*.py"):
        for imported_name in _absolute_imports(path):
            root = imported_name.partition(".")[0]
            if root in forbidden_roots:
                invalid.append((path.relative_to(INTEGRATIONS_ROOT), imported_name))

    assert invalid == []
