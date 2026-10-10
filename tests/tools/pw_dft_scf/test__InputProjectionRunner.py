from __future__ import annotations

import hashlib
import importlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unittest
from dataclasses import asdict
from pathlib import Path
from types import ModuleType

from tools.pw_dft_scf.environment import (
    WorkflowRunnerEnvironment,
)
from tools.pw_dft_scf.render_inputs import (
    InputProjectionRunner,
)

_FIXTURE_SHA256 = "bfc9f867474c86d20359a23563cf3d6277928bcf435a126357fd2bdc4732f57e"
_CAMPAIGN_SIMULATION_IDS = {
    "silicon-scf-qe": "Si.PrimitiveUnitCell.QE.SCF.Single",
    "silicon-kpoints-qe": "Si.PrimitiveUnitCell.QE.SCF.ConvergenceBase",
    "silicon-encut-qe": "Si.PrimitiveUnitCell.QE.SCF.ConvergenceBase",
    "silicon-cross-qe": "Si.PrimitiveUnitCell.QE.SCF.ConvergenceBase",
    "silicon-scf-vasp": "Si.PrimitiveUnitCell.VASP.SCF.Single",
    "silicon-kpoints-vasp": "Si.PrimitiveUnitCell.VASP.SCF.Single",
    "silicon-encut-vasp": "Si.PrimitiveUnitCell.VASP.SCF.Single",
    "silicon-cross-vasp": "Si.PrimitiveUnitCell.VASP.SCF.Single",
}
_CAMPAIGN_RELOCATIONS = {
    "silicon-scf-qe": "campaigns/qe-single.toml",
    "silicon-kpoints-qe": "campaigns/qe-kpoint.toml",
    "silicon-encut-qe": "campaigns/qe-cutoff.toml",
    "silicon-cross-qe": "campaigns/qe-grid.toml",
    "silicon-scf-vasp": "campaigns/vasp-single.toml",
    "silicon-kpoints-vasp": "campaigns/vasp-kpoint.toml",
    "silicon-encut-vasp": "campaigns/vasp-cutoff.toml",
    "silicon-cross-vasp": "campaigns/vasp-grid.toml",
}


class InputProjectionRunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = Path(__file__).resolve().parents[3]
        self.example = self.repository / "examples/workflows/pw_dft_scf"
        fixture_path = (
            self.repository / "tests/fixtures/pw_dft_scf/campaign-projections.json"
        )
        fixture_bytes = fixture_path.read_bytes()
        self.assertEqual(hashlib.sha256(fixture_bytes).hexdigest(), _FIXTURE_SHA256)
        self.fixture = json.loads(fixture_bytes)

    def test_exact_eight_campaign_matrix_and_rendered_values(self) -> None:
        environment = WorkflowRunnerEnvironment.load(
            self.repository / "tools/pw_dft_scf/config/runner.toml"
        )
        expected_paths = {
            _CAMPAIGN_RELOCATIONS[item["campaign_id"]]
            for item in self.fixture["campaigns"]
        }
        discovered_paths = {
            path.relative_to(self.example).as_posix()
            for path in (self.example / "campaigns").glob("*.toml")
        }
        self.assertEqual(discovered_paths, expected_paths)

        with tempfile.TemporaryDirectory() as temporary_directory:
            for index, expected in enumerate(self.fixture["campaigns"]):
                campaign_path = (
                    self.example / _CAMPAIGN_RELOCATIONS[expected["campaign_id"]]
                )
                declaration = tomllib.loads(campaign_path.read_text(encoding="utf-8"))
                self.assertEqual(declaration["campaign_id"], expected["campaign_id"])
                self.assertEqual(declaration["mode"], expected["mode"])
                self.assertEqual(declaration["integration"], expected["provider"])
                self.assertEqual(
                    declaration["simulation_id"],
                    _CAMPAIGN_SIMULATION_IDS[expected["campaign_id"]],
                )
                self.assertNotIn("structure_id", declaration)
                self.assertNotIn("sampling_profile", declaration)
                self.assertEqual(
                    declaration.get("coordinate_profile"),
                    expected["coordinate_profile"],
                )
                self.assertEqual(
                    declaration.get("policy_profile"), expected["policy_profile"]
                )

                loaded = environment.loader.load(campaign_path)
                recipe = loaded.campaign.recipe
                request = recipe.base_request
                self.assertEqual(type(recipe).__name__, expected["recipe_type"])
                self.assertEqual(recipe.campaign_id, expected["campaign_id"])
                self.assertEqual(
                    loaded.campaign.integration_id.value, expected["provider"]
                )
                self.assertEqual(
                    loaded.projection_profile_id, expected["projection_profile"]
                )
                self.assertEqual(
                    list(request.specification.kpoint_sampling.mesh),
                    expected["sampling"]["kpoint_mesh"],
                )
                self.assertEqual(
                    list(request.specification.kpoint_sampling.shift),
                    expected["sampling"]["kpoint_shift"],
                )
                self.assertEqual(
                    request.specification.wavefunction_cutoff_ev,
                    expected["sampling"]["wavefunction_cutoff_ev"],
                )
                self.assertEqual(
                    list(getattr(recipe, "mesh_densities", ())) or None,
                    expected["mesh_densities"],
                )
                self.assertEqual(
                    list(getattr(recipe, "wavefunction_cutoffs_ev", ())) or None,
                    expected["wavefunction_cutoffs_ev"],
                )
                policy = getattr(recipe, "policy", None)
                self.assertEqual(
                    asdict(policy) if policy is not None else None, expected["policy"]
                )

                positions = [
                    atom.position_fractional.magnitude.tolist()
                    for atom in loaded.structure.unit_cell.atomic_basis.atoms
                ]
                self.assertEqual(positions, [[0.0, 0.0, 0.0], [0.25, 0.25, 0.25]])
                output = Path(temporary_directory) / str(index)
                rendered = InputProjectionRunner(environment).render(
                    campaign_path, output
                )
                actual_hashes = {
                    path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in rendered
                }
                # The immutable transferred fixture still identifies the former
                # projection-envelope bytes. The atomic prepared-input migration
                # deliberately replaces only that envelope while retaining the
                # calculator filenames and independently checking their new exact
                # content identities through CalculatorInputRecord.
                self.assertEqual(
                    set(actual_hashes) - {"calculator-input-record.json"},
                    set(expected["rendered_sha256"]) - {"input-projection.json"},
                )
                prepared_payload = json.loads(
                    (output / "calculator-input-record.json").read_bytes()
                )
                self.assertEqual(
                    {
                        artifact["filename"]: artifact["sha256"]
                        for artifact in prepared_payload["artifacts"]
                    },
                    {
                        name: sha256
                        for name, sha256 in actual_hashes.items()
                        if name != "calculator-input-record.json"
                    },
                )
                rendered_text = "\n".join(
                    path.read_text(encoding="ascii")
                    for path in rendered
                    if path.suffix != ".json"
                )
                for fragment in expected["rendered_fragments"]:
                    self.assertIn(fragment, rendered_text)

    def test_exact_archive_provider_graph(self) -> None:
        simulations_repository = self.repository
        commit = self.fixture["simulations_commit"]
        tree = subprocess.run(
            ["git", "rev-parse", f"{commit}^{{tree}}"],
            cwd=simulations_repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(tree, self.fixture["simulations_tree"])
        archive = subprocess.run(
            ["git", "archive", commit, "--", "src/python"],
            cwd=simulations_repository,
            check=True,
            capture_output=True,
        ).stdout
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive_root = Path(temporary_directory)
            with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as source:
                source.extractall(archive_root, filter="data")
            provider_root = archive_root / "src/python"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    str(
                        self.repository / "tests/support/exact_provider_graph_probe.py"
                    ),
                    "--provider-root",
                    str(provider_root),
                    "--repository",
                    str(self.repository),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        loaded = json.loads(completed.stdout)
        expected_modules = {
            item["module"]: {
                "path": item["path"].removeprefix("src/python/"),
                "sha256": item["sha256"],
            }
            for item in self.fixture["provider_modules"]
        }
        self.assertEqual(loaded, expected_modules)
        for expected in self.fixture["provider_modules"]:
            entry = (
                subprocess.run(
                    ["git", "ls-tree", commit, "--", expected["path"]],
                    cwd=simulations_repository,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                .stdout.strip()
                .split()
            )
            self.assertEqual(entry[:3], ["100644", "blob", expected["git_blob"]])

    def test_current_provider_modules_are_repository_owned(self) -> None:
        for expected in self.fixture["provider_modules"]:
            module = importlib.import_module(expected["module"])
            self._assert_current_head_module(module, expected["path"])

    def _assert_current_head_module(self, module: ModuleType, path: str) -> None:
        module_path = Path(module.__file__ or "").resolve()
        expected_path = (self.repository / path).resolve()
        self.assertTrue(module_path.is_file())
        self.assertEqual(
            hashlib.sha256(module_path.read_bytes()).hexdigest(),
            hashlib.sha256(expected_path.read_bytes()).hexdigest(),
        )
        entry = subprocess.run(
            ["git", "ls-tree", "HEAD", "--", path],
            cwd=self.repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split()
        self.assertEqual(len(entry), 4)
        self.assertEqual(entry[:2], ["100644", "blob"])


if __name__ == "__main__":
    unittest.main()
