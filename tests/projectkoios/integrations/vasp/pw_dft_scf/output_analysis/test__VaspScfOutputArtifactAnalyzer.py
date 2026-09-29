from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from projectkoios.integrations.vasp.data_extraction import (
    VaspDataArtifactError,
    VaspDataSourceExtractor,
)
from projectkoios.integrations.vasp.pw_dft_scf.output_analysis import (
    VaspScfArtifactError,
    VaspScfData,
    VaspScfDataExtractor,
    VaspScfOutputArtifactAnalyzer,
)
from projectkoios.integrations.vasp.pw_dft_scf.projection import (
    VASP_SCF_INTEGRATION_ID,
)
from tests.projectkoios.integrations.vasp.outcar import (
    test__VaspOutcarParser as outcar_test,
)
from tests.projectkoios.integrations.vasp.run_xml import (
    test__VaspRunXmlParser as run_xml_test,
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

    def test_facades_outcar_execution_and_optional_run_xml(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run = root / "run"
            run.mkdir()
            (run / "OUTCAR").write_text(outcar_test.OUTCAR, encoding="utf-8")
            (run / "vasprun.xml").write_bytes(run_xml_test.VASPRUN_XML)
            (run / "vasp.out").write_bytes(b"captured stdout\n")
            (run / "vasp.err").write_bytes(b"")
            (run / "WAVECAR").write_bytes(b"binary-wavefunction-evidence")
            (run / "execution.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "status": "succeeded",
                        "returncode": 0,
                        "stdout_filename": "vasp.out",
                        "stderr_filename": "vasp.err",
                    }
                ),
                encoding="utf-8",
            )

            data = VaspScfDataExtractor(root).extract("run/OUTCAR")

        self.assertIsInstance(data, VaspScfData)
        self.assertIsNotNone(data.sources.vasprun)
        self.assertEqual(
            data.sources.artifact("vasprun").byte_size, len(run_xml_test.VASPRUN_XML)
        )
        self.assertEqual(data.sources.artifact("stdout").relative_path, "run/vasp.out")
        self.assertEqual(data.sources.artifact("wavecar").byte_size, 28)
        self.assertEqual(
            data.sources.artifact("wavecar").sha256,
            hashlib.sha256(b"binary-wavefunction-evidence").hexdigest(),
        )
        self.assertTrue(data.consistency.outcar_completion_matches_execution)
        self.assertFalse(data.consistency.vasprun_program_version_matches)
        self.assertTrue(data.consistency.vasprun_atom_count_matches)
        self.assertFalse(data.consistency.vasprun_kpoint_count_matches)
        self.assertFalse(data.consistency.vasprun_total_energy_matches)
        self.assertIs(
            data.observation.native_artifact.integration_id, VASP_SCF_INTEGRATION_ID
        )

    def test_large_identity_artifact_enforces_limit_during_growth(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            wavecar = _write_generic_run(root, wavecar=b"12345")
            observed = wavecar.lstat()
            initial_observation = SimpleNamespace(
                st_mode=observed.st_mode,
                st_dev=observed.st_dev,
                st_ino=observed.st_ino,
                st_size=4,
                st_mtime_ns=observed.st_mtime_ns,
                st_ctime_ns=observed.st_ctime_ns,
            )

            with (
                patch.object(
                    Path,
                    "lstat",
                    return_value=initial_observation,
                ),
                self.assertRaisesRegex(
                    VaspDataArtifactError,
                    "identity artifact exceeds byte limit",
                ),
            ):
                VaspDataSourceExtractor(
                    root,
                    maximum_identity_artifact_bytes=4,
                ).extract("run/OUTCAR")

    def test_large_identity_artifact_rejects_concurrent_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            wavecar = _write_generic_run(root, wavecar=b"stable evidence")
            observed = wavecar.lstat()
            before = SimpleNamespace(
                st_mode=observed.st_mode,
                st_dev=observed.st_dev,
                st_ino=observed.st_ino,
                st_size=observed.st_size,
                st_mtime_ns=observed.st_mtime_ns,
                st_ctime_ns=observed.st_ctime_ns,
            )
            after = SimpleNamespace(
                st_mode=observed.st_mode,
                st_dev=observed.st_dev,
                st_ino=observed.st_ino,
                st_size=observed.st_size,
                st_mtime_ns=observed.st_mtime_ns + 1,
                st_ctime_ns=observed.st_ctime_ns + 1,
            )

            with (
                patch(
                    "projectkoios.integrations.vasp.data_extraction.os.fstat",
                    side_effect=(before, after),
                ),
                self.assertRaisesRegex(
                    VaspDataArtifactError,
                    "changed while hashing",
                ),
            ):
                VaspDataSourceExtractor(root).extract("run/OUTCAR")

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


def _write_generic_run(root: Path, *, wavecar: bytes) -> Path:
    run = root / "run"
    run.mkdir()
    (run / "OUTCAR").write_text(outcar_test.OUTCAR, encoding="utf-8")
    (run / "execution.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "succeeded",
                "returncode": 0,
                "stdout_filename": None,
                "stderr_filename": None,
            }
        ),
        encoding="utf-8",
    )
    path = run / "WAVECAR"
    path.write_bytes(wavecar)
    return path


if __name__ == "__main__":
    unittest.main()
