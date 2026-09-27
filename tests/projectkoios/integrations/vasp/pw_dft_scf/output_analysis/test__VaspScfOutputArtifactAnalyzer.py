from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import pytest

from projectkoios.integrations.vasp.pw_dft_scf.output_analysis import (
    VaspScfArtifactError,
    VaspScfOutputArtifactAnalyzer,
)
from projectkoios.integrations.vasp.pw_dft_scf.projection import (
    VASP_SCF_INTEGRATION_ID,
)
from tests.projectkoios.integrations.vasp.outcar import (
    test__VaspOutcarParser as outcar_test,
)
from tests.support.repository_root import REPOSITORY_ROOT

pytestmark = pytest.mark.integration

_FAILURE_EVIDENCE = (
    REPOSITORY_ROOT / "examples/projectkoios/integrations/vasp/pw_dft_scf/"
    "Si/primitive/evidence/failures/negative-lattice-orientation"
)


class VaspScfOutputArtifactAnalyzerTest(unittest.TestCase):
    def test_normalizes_successful_retained_outcar(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run = root / "run"
            run.mkdir()
            (run / "OUTCAR").write_text(outcar_test.OUTCAR, encoding="utf-8")
            (run / "execution.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "status": "succeeded",
                        "returncode": 0,
                    }
                ),
                encoding="utf-8",
            )

            observation = VaspScfOutputArtifactAnalyzer(root).analyze("run/OUTCAR")

        self.assertEqual(observation.total_energy_ev, -10.84056782)
        self.assertEqual(observation.total_energy_ev_per_atom, -5.42028391)
        self.assertEqual(
            observation.native_artifact.integration_id,
            VASP_SCF_INTEGRATION_ID,
        )
        self.assertTrue(observation.completed)
        self.assertTrue(observation.converged)

    def test_captures_zero_returncode_negative_lattice_failure(self) -> None:
        manifest = json.loads(
            (_FAILURE_EVIDENCE / "manifest.json").read_text(encoding="utf-8")
        )
        for filename, declaration in manifest["artifacts"].items():
            if not declaration.get("committed", True):
                continue
            payload = (_FAILURE_EVIDENCE / filename).read_bytes()
            with self.subTest(filename=filename):
                self.assertEqual(len(payload), declaration["byte_size"])
                self.assertEqual(
                    hashlib.sha256(payload).hexdigest(),
                    declaration["sha256"],
                )

        with self.assertRaises(VaspScfArtifactError) as caught:
            VaspScfOutputArtifactAnalyzer(_FAILURE_EVIDENCE).analyze("OUTCAR")

        self.assertEqual(caught.exception.code, "negative-lattice-orientation")
        self.assertEqual(
            caught.exception.native_artifact.artifact_id,
            "vasp.out",
        )
        self.assertEqual(
            caught.exception.native_artifact.sha256,
            manifest["artifacts"]["vasp.out"]["sha256"],
        )

    def test_rejects_artifact_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            outside = root.parent / "outside-OUTCAR"
            outside.write_text(outcar_test.OUTCAR, encoding="utf-8")
            try:
                with self.assertRaisesRegex(ValueError, "inside artifact_root"):
                    VaspScfOutputArtifactAnalyzer(root).analyze("../outside-OUTCAR")
            finally:
                outside.unlink()


if __name__ == "__main__":
    unittest.main()
