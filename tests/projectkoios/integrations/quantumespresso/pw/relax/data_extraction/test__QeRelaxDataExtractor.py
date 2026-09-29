from __future__ import annotations

import hashlib
import io
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (
    QePwDataSources,
)
from projectkoios.integrations.quantumespresso.pw.relax.data_extraction import (  # noqa: E501
    QeRelaxDataExtractor,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.data import QeRelaxData

_STDOUT = b"""Program PWSCF v.7.5 starts on 1Jan2026
axis vectors are left-handed
! total energy = -10.001000 Ry
convergence has been achieved in 3 iterations
energy new = -10.000900 Ry
bfgs converged in 3 scf cycles and 2 bfgs steps
(criteria: energy < 1.0E-04, force < 1.0E-03)
End of BFGS Geometry Optimization
Final energy = -10.001000 Ry
Begin final coordinates
ATOMIC_POSITIONS (alat)
Si 0.000000 0.000000 0.000000
Si 0.250000 0.250000 0.250000
End final coordinates
JOB DONE.
"""
_STDERR = b"IEEE_UNDERFLOW_FLAG\n"


@dataclass(frozen=True, slots=True)
class _ParsedQexsdDocument:
    source_path: str = "/evidence/data-file-schema.xml"
    source_sha256: str = "a" * 64
    source_byte_count: int = 123
    qexsd_version: str = "25.05.21"
    producing_application: str = "Quantum ESPRESSO"
    producing_application_version: str | None = "7.5"
    declared_unit_system_label: str = "Hartree atomic units"
    atomic_structure_alat: float = 2.0
    direct_lattice_vectors: tuple[tuple[float, float, float], ...] = (
        (2.0, 0.0, 0.0),
        (0.0, 2.0, 0.0),
        (0.0, 0.0, 2.0),
    )
    direct_lattice_source_label: str = "output/atomic_structure/cell/a1,a2,a3"
    atoms: tuple[tuple[int, str, tuple[float, float, float]], ...] = (
        (1, "Si", (0.0, 0.0, 0.0)),
        (2, "Si", (0.5, 0.5, 0.5)),
    )
    declared_atom_count: int = 2
    atomic_positions_source_label: str = "output/atomic_structure/atomic_positions"
    exit_status: int = 0


class QeRelaxDataExtractorTest(unittest.TestCase):
    def test_extracts_fixed_cell_native_data(self) -> None:
        data = QeRelaxDataExtractor().extract(
            stdout_payload=_STDOUT,
            stderr_payload=_STDERR,
            stdout_relative_path="run/pw.out",
            stderr_relative_path="run/pw.err",
        )

        self.assertIsInstance(data, QeRelaxData)
        self.assertIsInstance(data.sources, QePwDataSources)
        self.assertEqual(data.calculation, "relax")
        self.assertIs(data.stdout, data.streams.stdout)
        self.assertIs(data.stderr, data.streams.stderr)
        self.assertEqual(
            data.stdout_artifact.sha256,
            hashlib.sha256(_STDOUT).hexdigest(),
        )
        self.assertTrue(data.job_completed)
        self.assertTrue(data.optimizer_converged)
        self.assertTrue(data.stdout.left_handed_axis_warning)
        self.assertAlmostEqual(data.streams.stdout.bfgs_energy_change_ry, 0.0001)
        self.assertEqual(len(data.steps), 1)
        self.assertEqual(data.trajectory.steps[0].total_energy_ry, -10.001)
        self.assertIsNotNone(data.trajectory.steps[0].emitted_positions)
        self.assertEqual(
            data.streams.stderr.ieee_flags,
            ("IEEE_UNDERFLOW_FLAG",),
        )
        self.assertIsNone(data.qexsd)
        self.assertIsNone(data.final_structure)
        self.assertFalse(data.consistency.qexsd_present)
        self.assertIsNone(data.execution)

    def test_streams_exact_stdout_to_storage_and_returns_data_facade(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "pw.out"
            data = QeRelaxDataExtractor().extract_stream(
                stdout_source=io.BytesIO(_STDOUT),
                stdout_destination=destination,
                stderr_payload=_STDERR,
                stdout_relative_path="run/pw.out",
                stderr_relative_path="run/pw.err",
            )
            persisted = destination.read_bytes()

        self.assertEqual(persisted, _STDOUT)
        self.assertEqual(data.stdout_artifact.byte_size, len(_STDOUT))
        self.assertEqual(
            data.stdout_artifact.sha256,
            hashlib.sha256(_STDOUT).hexdigest(),
        )
        self.assertTrue(data.job_completed)
        self.assertTrue(data.optimizer_converged)
        self.assertEqual(data.trajectory.steps[0].total_energy_ry, -10.001)

    def test_facades_the_complete_qexsd_document_and_interpreted_structure(
        self,
    ) -> None:
        document = _ParsedQexsdDocument()

        data = QeRelaxDataExtractor().extract(
            stdout_payload=_STDOUT,
            stderr_payload=_STDERR,
            qexsd_document=document,
        )

        self.assertIsNotNone(data.qexsd)
        assert data.qexsd is not None
        self.assertIs(data.qexsd.document, document)
        self.assertIs(data.final_structure, data.qexsd.final_structure)
        self.assertTrue(data.consistency.qexsd_present)
        self.assertTrue(data.consistency.terminal_status_matches)
        self.assertIsNone(data.consistency.atom_count_matches)

    def test_does_not_manufacture_success_from_empty_stderr(self) -> None:
        data = QeRelaxDataExtractor().extract(
            stdout_payload=b"Program PWSCF v.7.5\n",
            stderr_payload=b"",
        )

        self.assertFalse(data.streams.stdout.job_completed)
        self.assertFalse(data.streams.stdout.geometry_optimization_converged)
        self.assertEqual(data.trajectory.steps, ())
        self.assertEqual(data.streams.stderr.ieee_flags, ())


if __name__ == "__main__":
    unittest.main()
