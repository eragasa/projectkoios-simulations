from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class BandReferenceEvidenceTest(unittest.TestCase):
    def test_neutral_silicon_path_is_bound_to_the_canonical_structure(self) -> None:
        root = Path(__file__).resolve().parents[2]
        directory = root / "examples/projectkoios/simulations/dft/pw/Si/primitive"
        structure_path = directory / "Si.primitive.json"
        path_declaration = json.loads(
            (directory / "Si.primitive.fcc-band-path.json").read_text(encoding="utf-8")
        )
        structure = json.loads(structure_path.read_text(encoding="utf-8"))

        self.assertEqual(structure["structure_id"], "Si.primitive")
        self.assertEqual(
            path_declaration["structure"]["sha256"],
            hashlib.sha256(structure_path.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            path_declaration["coordinate_system"],
            "reciprocal-fractional",
        )
        self.assertEqual(
            tuple(structure["lattice"]["A"][key] for key in ("a1", "a2", "a3")),
            (
                [0.5, 0.5, 0.0],
                [0.0, 0.5, 0.5],
                [0.5, 0.0, 0.5],
            ),
        )

    def test_retained_inputs_match_manifests_without_granting_execution(self) -> None:
        root = Path(__file__).resolve().parents[2]
        qe = root / "examples/projectkoios/integrations/quantumespresso/pw/bands/Si"
        vasp = root / "examples/projectkoios/integrations/vasp/bands/Si/primitive"
        manifests = (
            (
                qe / "primitive/reference-software-observation/manifest.json",
                "current_canonical_unit_cell_basis",
                True,
            ),
            (
                qe / "primitive/superseded-cyclic-basis-observation/manifest.json",
                "superseded_noncanonical_unit_cell_basis",
                False,
            ),
            (
                vasp / "reference-software-observation/manifest.json",
                "current_canonical_unit_cell_basis",
                True,
            ),
            (
                vasp / "superseded-cyclic-basis-observation/manifest.json",
                "superseded_noncanonical_unit_cell_basis",
                False,
            ),
        )

        for manifest_path, expected_status, canonical in manifests:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(
                manifest["evidence_kind"],
                "authorized_software_integration_observation",
            )
            self.assertEqual(manifest["status"], expected_status)
            self.assertFalse(manifest["authorization"]["reusable_execution_authority"])
            self.assertRegex(
                manifest["calculator"]["executable_sha256"],
                _SHA256,
            )
            if canonical:
                structure = root / manifest["structure"]["repository_path"]
                self.assertEqual(
                    hashlib.sha256(structure.read_bytes()).hexdigest(),
                    manifest["structure"]["sha256"],
                )
            for declaration in manifest["retained_inputs"]:
                retained = manifest_path.parent / declaration["path"]
                payload = retained.read_bytes()
                self.assertEqual(len(payload), declaration["byte_count"])
                self.assertEqual(
                    hashlib.sha256(payload).hexdigest(),
                    declaration["sha256"],
                )
            for declaration in manifest["external_artifact_identities"]:
                self.assertGreaterEqual(declaration["byte_count"], 0)
                self.assertRegex(declaration["sha256"], _SHA256)
            self.assertEqual(
                manifest["claims"]["canonical_Si_primitive_projection_established"],
                canonical,
            )
            self.assertFalse(manifest["claims"]["convergence_established"])
            self.assertFalse(manifest["claims"]["scientific_validation_established"])


if __name__ == "__main__":
    unittest.main()
