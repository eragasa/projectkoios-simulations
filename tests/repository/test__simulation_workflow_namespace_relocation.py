from __future__ import annotations

import ast
import hashlib
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = "0ca21564730015dcf989200858b0a6de3f26a038"
OLD_NAMESPACE = "projectkoios.simulation_workflows"
NEW_NAMESPACE = "projectkoios.simulations.workflows"
OLD_SOURCE = "src/python/projectkoios/simulation_workflows"
NEW_SOURCE = "src/python/projectkoios/simulations/workflows"
OLD_TESTS = "tests/projectkoios/simulation_workflows"
NEW_TESTS = "tests/projectkoios/simulations/workflows"
OLD_DOCS = "docs/architecture/projectkoios/simulation_workflows"
NEW_DOCS = "docs/architecture/projectkoios/simulations/workflows"
FIXTURE = "tests/fixtures/pw_dft_scf/qe-retained-convergence-normalized.json"
FIXTURE_SHA256 = "ff751aa7aeccc467886ec74979c7b2a92cdc645c83e4917e460bee36db6361d3"


def _git(*arguments: str, text: bool = True) -> str | bytes:
    completed = subprocess.run(
        ("git", "-C", str(REPOSITORY_ROOT), *arguments),
        check=True,
        capture_output=True,
        text=text,
    )
    return completed.stdout


def _base_paths(root: str) -> tuple[str, ...]:
    output = _git("ls-tree", "-r", "--name-only", BASE_COMMIT, "--", root)
    assert isinstance(output, str)
    return tuple(output.splitlines())


def _base_bytes(path: str) -> bytes:
    output = _git("show", f"{BASE_COMMIT}:{path}", text=False)
    assert isinstance(output, bytes)
    return output


def _normalized_text(payload: bytes) -> str:
    return payload.decode("utf-8").replace(OLD_NAMESPACE, NEW_NAMESPACE)


def _ast_shape(node: ast.AST | list[ast.AST] | None) -> str:
    if node is None:
        return "None"
    if isinstance(node, list):
        return "[" + ",".join(ast.dump(item) for item in node) + "]"
    return ast.dump(node)


def _module_shape(source: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    tree = ast.parse(source)
    imports = tuple(
        sorted(
            ast.dump(node)
            for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        )
    )
    definitions = tuple(
        ast.dump(node)
        for node in tree.body
        if not isinstance(node, (ast.Import, ast.ImportFrom))
    )
    return imports, definitions


def _api_manifest(source: str) -> tuple[tuple[str, str, str], ...]:
    tree = ast.parse(source)
    records: list[tuple[str, str, str]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                records.append(
                    (
                        node.name,
                        type(node).__name__,
                        _ast_shape(node.args) + _ast_shape(node.returns),
                    )
                )
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            records.append(
                (
                    node.name,
                    "ClassDef",
                    _ast_shape(node.bases) + _ast_shape(node.keywords),
                )
            )
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not child.name.startswith("_"):
                        records.append(
                            (
                                f"{node.name}.{child.name}",
                                type(child).__name__,
                                _ast_shape(child.args) + _ast_shape(child.returns),
                            )
                        )
                elif (
                    isinstance(child, ast.AnnAssign)
                    and isinstance(child.target, ast.Name)
                    and not child.target.id.startswith("_")
                ):
                    records.append(
                        (
                            f"{node.name}.{child.target.id}",
                            "AnnAssign",
                            _ast_shape(child.annotation) + _ast_shape(child.value),
                        )
                    )
    return tuple(records)


def test_source_and_tests_are_an_exact_normalized_move() -> None:
    old_sources = _base_paths(OLD_SOURCE)
    assert len(old_sources) == 28
    for old_path in old_sources:
        relative = old_path.removeprefix(f"{OLD_SOURCE}/")
        if relative == "py.typed":
            assert (
                _base_bytes(old_path)
                == (
                    REPOSITORY_ROOT / "src/python/projectkoios/simulations/py.typed"
                ).read_bytes()
            )
            continue
        new_path = REPOSITORY_ROOT / NEW_SOURCE / relative
        assert _module_shape(new_path.read_text(encoding="utf-8")) == _module_shape(
            _normalized_text(_base_bytes(old_path))
        )

    old_tests = _base_paths(OLD_TESTS)
    assert len(old_tests) == 11
    for old_path in old_tests:
        relative = old_path.removeprefix(f"{OLD_TESTS}/")
        expected = _normalized_text(_base_bytes(old_path))
        if relative == "pw_dft_scf/replay/test__retained_qe_evidence.py":
            expected = expected.replace(".parents[4]", ".parents[5]")
        new_path = REPOSITORY_ROOT / NEW_TESTS / relative
        assert _module_shape(new_path.read_text(encoding="utf-8")) == _module_shape(
            expected
        )


def test_documentation_indexes_preserve_moved_node_inventory() -> None:
    old_indexes = tuple(
        path for path in _base_paths(OLD_DOCS) if path.endswith("/index.md")
    )
    assert len(old_indexes) == 54
    for old_path in old_indexes:
        relative = old_path.removeprefix(f"{OLD_DOCS}/")
        new_path = REPOSITORY_ROOT / NEW_DOCS / relative
        assert new_path.is_file(), relative
        assert new_path.read_text(encoding="utf-8").strip(), relative


def test_public_api_signatures_are_unchanged_by_relocation() -> None:
    old_sources = tuple(
        path for path in _base_paths(OLD_SOURCE) if path.endswith(".py")
    )
    old_manifest: dict[str, tuple[tuple[str, str, str], ...]] = {}
    new_manifest: dict[str, tuple[tuple[str, str, str], ...]] = {}
    for old_path in old_sources:
        relative = old_path.removeprefix(f"{OLD_SOURCE}/")
        old_manifest[relative] = _api_manifest(_normalized_text(_base_bytes(old_path)))
        new_manifest[relative] = _api_manifest(
            (REPOSITORY_ROOT / NEW_SOURCE / relative).read_text(encoding="utf-8")
        )

    assert new_manifest == old_manifest


def test_relocation_preserves_fixture_and_stable_action_identity() -> None:
    fixture = REPOSITORY_ROOT / FIXTURE
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == FIXTURE_SHA256

    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPOSITORY_ROOT / NEW_SOURCE).rglob("*.py")
    )
    assert "projectkoios.applications.pw-dft-scf.convergence-replay" in source_text
    assert OLD_NAMESPACE not in source_text
