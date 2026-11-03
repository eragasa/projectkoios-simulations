from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pytest

from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (
    QePwDataSources,
)
from projectkoios.integrations.quantumespresso.pw.scf import (
    data_extraction as qe_data_extraction,
)
from projectkoios.physkit.units import (
    ModelSystemUnitConverter,
    PhysicalUnit,
    ScalarQuantity,
)
from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfDiagnosticSeverity,
)
from tests.projectkoios.integrations.quantumespresso.pw.scf import (
    support as qe_support,
)
from tests.projectkoios.integrations.quantumespresso.resources.qexsd_fixtures import (
    QEXSD_FIXTURES,
)

pytestmark = pytest.mark.integration

MAXIMUM_TEST_ARTIFACT_BYTES = 200


class QeScfDataExtractorTest(unittest.TestCase):
    def test__QeScfDataExtractor__preserves_retained_qe_values_and_ieee_warnings(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_successful_run(root)

            data = qe_data_extraction.QeScfDataExtractor(artifact_root=root).extract(
                "run/pw.out"
            )

        self.assertIsInstance(data, qe_data_extraction.QeScfData)
        self.assertIsInstance(data.sources, QePwDataSources)
        self.assertIs(data.observation.native_artifact, data.native_artifact)
        self.assertEqual(data.execution.status, "succeeded")
        self.assertEqual(data.execution_artifact.relative_path, "run/execution.json")
        self.assertIsNone(data.qexsd)
        self.assertTrue(data.consistency.stdout_completion_matches_execution)
        observation = data

        expected_energy = ModelSystemUnitConverter.convert_scalar(
            ScalarQuantity(
                magnitude=qe_support.EXPECTED_TOTAL_ENERGY_RY,
                unit=PhysicalUnit(expression="Ry"),
            ),
            PhysicalUnit(expression="eV"),
        ).magnitude
        expected_cutoff = ModelSystemUnitConverter.convert_scalar(
            ScalarQuantity(
                magnitude=qe_support.EXPECTED_WAVEFUNCTION_CUTOFF_RY,
                unit=PhysicalUnit(expression="Ry"),
            ),
            PhysicalUnit(expression="eV"),
        ).magnitude
        self.assertAlmostEqual(observation.total_energy_ev, expected_energy)
        self.assertAlmostEqual(
            observation.wavefunction_cutoff_ev or 0.0, expected_cutoff
        )
        self.assertEqual(observation.atom_count, qe_support.EXPECTED_ATOM_COUNT)
        self.assertEqual(
            observation.program_version,
            qe_support.EXPECTED_PROGRAM_VERSION,
        )
        self.assertEqual(
            observation.electronic_iteration_count,
            qe_support.EXPECTED_ELECTRONIC_ITERATION_COUNT,
        )
        self.assertEqual(
            observation.irreducible_kpoint_count,
            qe_support.EXPECTED_IRREDUCIBLE_KPOINT_COUNT,
        )
        self.assertTrue(observation.completed)
        self.assertTrue(observation.converged)
        self.assertEqual(
            tuple(item.code for item in observation.diagnostics),
            (
                "ieee-invalid-flag",
                "ieee-divide-by-zero",
                "ieee-overflow-flag",
                "ieee-underflow-flag",
            ),
        )
        self.assertTrue(
            all(
                item.severity is PwDftScfDiagnosticSeverity.WARNING
                for item in observation.diagnostics
            )
        )
        self.assertTrue(
            all(
                item.native_artifact.artifact_id == "run/pw.err"
                for item in observation.diagnostics
            )
        )

    def test__QeScfDataExtractor__normalizes_collinear_total_magnetization(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run = self._write_successful_run(root)
            magnetic_output = qe_support.QE_PW_OUTPUT.replace(
                "JOB DONE.",
                "     total magnetization = 0.74 Bohr mag/cell\n"
                "     absolute magnetization = 0.83 Bohr mag/cell\n"
                "JOB DONE.",
            )
            (run / "pw.out").write_text(magnetic_output, encoding="utf-8")

            data = qe_data_extraction.QeScfDataExtractor(artifact_root=root).extract(
                "run/pw.out"
            )

        self.assertEqual(data.total_magnetization_electrons, 0.74)
        self.assertEqual(data.observation.total_magnetization_electrons, 0.74)

    def test__QeScfDataExtractor__facades_optional_qexsd(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_successful_run(root)
            document = QEXSD_FIXTURES.scf_document()

            data = qe_data_extraction.QeScfDataExtractor(artifact_root=root).extract(
                "run/pw.out", qexsd_document=document
            )

        qexsd = data.qexsd
        assert qexsd is not None
        self.assertIs(qexsd.document, document)
        self.assertIs(data.final_structure, qexsd.final_structure)
        self.assertTrue(data.consistency.qexsd_terminal_status_matches)
        self.assertTrue(data.consistency.qexsd_atom_count_matches)
        self.assertEqual(data.observation.atom_count, qe_support.EXPECTED_ATOM_COUNT)

    def test__QeScfDataExtractor__rejects_output_not_named_by_execution_evidence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run = self._write_successful_run(root)
            mismatched_record = {
                **qe_support.QE_SUCCESSFUL_EXECUTION_RECORD,
                "stdout_filename": "different.out",
            }
            (run / "execution.json").write_text(
                json.dumps(mismatched_record),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                qe_data_extraction.QeScfArtifactError,
                "recorded stdout_filename",
            ):
                qe_data_extraction.QeScfDataExtractor(artifact_root=root).extract(
                    "run/pw.out"
                )

    def test__QeScfDataExtractor__rejects_an_output_larger_than_the_declared_bound(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_successful_run(root)

            with self.assertRaisesRegex(
                qe_data_extraction.QeScfArtifactError,
                "exceeds byte limit",
            ):
                qe_data_extraction.QeScfDataExtractor(
                    artifact_root=root,
                    maximum_artifact_bytes=MAXIMUM_TEST_ARTIFACT_BYTES,
                ).extract("run/pw.out")

    def _write_successful_run(self, root: Path) -> Path:
        run = root / "run"
        run.mkdir()
        (run / "pw.out").write_text(qe_support.QE_PW_OUTPUT, encoding="utf-8")
        (run / "pw.err").write_text(qe_support.QE_STDERR, encoding="utf-8")
        (run / "execution.json").write_text(
            json.dumps(qe_support.QE_SUCCESSFUL_EXECUTION_RECORD),
            encoding="utf-8",
        )
        return run


if __name__ == "__main__":
    unittest.main()
