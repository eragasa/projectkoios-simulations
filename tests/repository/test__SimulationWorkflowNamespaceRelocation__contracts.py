from __future__ import annotations

import ast
import hashlib
import subprocess
from collections.abc import Sequence
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
EVOLVED_SOURCE_AFTER_RELOCATION = frozenset(
    {"pw_dft_relaxation/composition.py", "pw_dft_scf/recipe.py"}
)
EVOLVED_TESTS_AFTER_RELOCATION = {
    "pw_dft_relaxation/composition/test__PwDftRelaxationComposer.py": (
        "pw_dft_relaxation/composition/test__PwDftRelaxationComposer__composition.py"
    ),
    "pw_dft_scf/recipe/test__PwDftScfRecipe.py": (
        "pw_dft_scf/recipe/test__PwDftScfRecipe.py"
    ),
    "support.py": "support.py",
}


class TestSimulationWorkflowNamespaceRelocation:
    """Verify the retained simulation-workflow namespace relocation."""

    def _git_text(self, *arguments: str) -> str:
        completed = subprocess.run(
            ("git", "-C", str(REPOSITORY_ROOT), *arguments),
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout

    def _git_bytes(self, *arguments: str) -> bytes:
        completed = subprocess.run(
            ("git", "-C", str(REPOSITORY_ROOT), *arguments),
            check=True,
            capture_output=True,
        )
        return completed.stdout

    def _base_paths(self, root: str) -> tuple[str, ...]:
        output = self._git_text("ls-tree", "-r", "--name-only", BASE_COMMIT, "--", root)
        return tuple(output.splitlines())

    def _base_bytes(self, path: str) -> bytes:
        return self._git_bytes("show", f"{BASE_COMMIT}:{path}")

    def _normalized_text(self, payload: bytes) -> str:
        return payload.decode("utf-8").replace(OLD_NAMESPACE, NEW_NAMESPACE)

    def _ast_shape(self, node: ast.AST | Sequence[ast.AST] | None) -> str:
        if node is None:
            return "None"
        if isinstance(node, Sequence):
            return "[" + ",".join(ast.dump(item) for item in node) + "]"
        return ast.dump(node)

    def _module_shape(self, source: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
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

    def _api_manifest(self, source: str) -> tuple[tuple[str, str, str], ...]:
        tree = ast.parse(source)
        records: list[tuple[str, str, str]] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    records.append(
                        (
                            node.name,
                            type(node).__name__,
                            self._ast_shape(node.args) + self._ast_shape(node.returns),
                        )
                    )
            elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                records.append(
                    (
                        node.name,
                        "ClassDef",
                        self._ast_shape(node.bases) + self._ast_shape(node.keywords),
                    )
                )
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not child.name.startswith("_"):
                            records.append(
                                (
                                    f"{node.name}.{child.name}",
                                    type(child).__name__,
                                    self._ast_shape(child.args)
                                    + self._ast_shape(child.returns),
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
                                self._ast_shape(child.annotation)
                                + self._ast_shape(child.value),
                            )
                        )
        return tuple(records)

    def test__SimulationWorkflowNamespaceRelocation__preserves_normalized_move(
        self,
    ) -> None:
        """Verify preserves normalized move."""
        old_sources = self._base_paths(OLD_SOURCE)
        assert len(old_sources) == 28
        for old_path in old_sources:
            relative = old_path.removeprefix(f"{OLD_SOURCE}/")
            if relative == "py.typed":
                assert (
                    self._base_bytes(old_path)
                    == (
                        REPOSITORY_ROOT / "src/python/projectkoios/simulations/py.typed"
                    ).read_bytes()
                )
                continue
            new_path = REPOSITORY_ROOT / NEW_SOURCE / relative
            if relative in EVOLVED_SOURCE_AFTER_RELOCATION:
                assert new_path.is_file()
                continue
            assert self._module_shape(
                new_path.read_text(encoding="utf-8")
            ) == self._module_shape(self._normalized_text(self._base_bytes(old_path)))

        old_tests = self._base_paths(OLD_TESTS)
        assert len(old_tests) == 11
        for old_path in old_tests:
            relative = old_path.removeprefix(f"{OLD_TESTS}/")
            expected = self._normalized_text(self._base_bytes(old_path))
            if relative == "pw_dft_scf/replay/test__retained_qe_evidence.py":
                expected = expected.replace(".parents[4]", ".parents[5]")
            evolved_relative = EVOLVED_TESTS_AFTER_RELOCATION.get(relative)
            new_path = REPOSITORY_ROOT / NEW_TESTS / (evolved_relative or relative)
            if evolved_relative is not None:
                assert new_path.is_file()
                continue
            assert self._module_shape(
                new_path.read_text(encoding="utf-8")
            ) == self._module_shape(expected)

    def test__SimulationWorkflowNamespaceRelocation__preserves_documentation(
        self,
    ) -> None:
        """Verify preserves documentation."""
        old_indexes = tuple(
            path for path in self._base_paths(OLD_DOCS) if path.endswith("/index.md")
        )
        assert len(old_indexes) == 54
        for old_path in old_indexes:
            relative = old_path.removeprefix(f"{OLD_DOCS}/")
            new_path = REPOSITORY_ROOT / NEW_DOCS / relative
            assert new_path.is_file(), relative
            assert new_path.read_text(encoding="utf-8").strip(), relative

    def test__SimulationWorkflowNamespaceRelocation__preserves_public_api(self) -> None:
        """Verify preserves public api."""
        old_sources = tuple(
            path for path in self._base_paths(OLD_SOURCE) if path.endswith(".py")
        )
        old_manifest: dict[str, tuple[tuple[str, str, str], ...]] = {}
        new_manifest: dict[str, tuple[tuple[str, str, str], ...]] = {}
        for old_path in old_sources:
            relative = old_path.removeprefix(f"{OLD_SOURCE}/")
            if relative in EVOLVED_SOURCE_AFTER_RELOCATION:
                continue
            old_manifest[relative] = self._api_manifest(
                self._normalized_text(self._base_bytes(old_path))
            )
            new_manifest[relative] = self._api_manifest(
                (REPOSITORY_ROOT / NEW_SOURCE / relative).read_text(encoding="utf-8")
            )

        assert new_manifest == old_manifest

    def test__SimulationWorkflowNamespaceRelocation__preserves_identity(self) -> None:
        """Verify preserves identity."""
        fixture = REPOSITORY_ROOT / FIXTURE
        assert hashlib.sha256(fixture.read_bytes()).hexdigest() == FIXTURE_SHA256

        source_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (REPOSITORY_ROOT / NEW_SOURCE).rglob("*.py")
        )
        assert "projectkoios.applications.pw-dft-scf.convergence-replay" in source_text
        assert OLD_NAMESPACE not in source_text
