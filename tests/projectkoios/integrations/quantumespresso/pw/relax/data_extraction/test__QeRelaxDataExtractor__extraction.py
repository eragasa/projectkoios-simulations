from __future__ import annotations

import hashlib
import io
import tempfile
import unittest
from pathlib import Path

import numpy as np

from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (
    QePwDataSources,
)
from projectkoios.integrations.quantumespresso.pw.relax.data_extraction import (  # noqa: E501
    QeRelaxDataExtractor,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.data import QeRelaxData
from projectkoios.physkit.mechanics.stress import StressSignConvention
from projectkoios.physkit.units import PhysicalUnit
from tests.projectkoios.integrations.quantumespresso.resources.qexsd_fixtures import (
    QEXSD_FIXTURES,
)
from tests.projectkoios.simulations.dft.pw.support import silicon_structure_resolution

_RELAX_DATA_EXTRACTOR = QeRelaxDataExtractor(
    stdout_relative_path="run/pw.out",
    stderr_relative_path="run/pw.err",
)

_STDOUT = b"""Program PWSCF v.7.5 starts on 1Jan2026
axis vectors are left-handed
! total energy = -10.001000 Ry
convergence has been achieved in 3 iterations
Forces acting on atoms (Cartesian axes, Ry/au):
atom 1 type 1 force = 0.000001 0.000000 0.000000
atom 2 type 1 force = -0.000001 0.000000 0.000000
Total force = 0.000002 Total SCF correction = 0.000000
 total stress (Ry/bohr**3) (kbar) P= 0.30
 0.000001 0.000000 0.000000 0.10 0.00 0.00
 0.000000 0.000002 0.000000 0.00 0.20 0.00
 0.000000 0.000000 0.000003 0.00 0.00 0.30
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


class QeRelaxDataExtractorTest(unittest.TestCase):
    def test__QeRelaxDataExtractor__extracts_fixed_cell_native_data(self) -> None:
        data = _RELAX_DATA_EXTRACTOR.extract(
            stdout_payload=_STDOUT,
            stderr_payload=_STDERR,
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
        assert data.streams.stdout.bfgs_energy_change_ry is not None
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

    def test__QeRelaxDataExtractor__streams_stdout_exactly(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "pw.out"
            data = _RELAX_DATA_EXTRACTOR.extract_stream(
                stdout_source=io.BytesIO(_STDOUT),
                stdout_destination=destination,
                stderr_payload=_STDERR,
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

    def test__QeRelaxDataExtractor__facades_qexsd_and_structure(
        self,
    ) -> None:
        document = QEXSD_FIXTURES.scf_document()

        data = _RELAX_DATA_EXTRACTOR.extract(
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

        starting_structure = silicon_structure_resolution()
        observation = data.normalize(starting_structure)

        assert observation.stress_tensor is not None
        self.assertEqual(
            observation.stress_tensor.components.unit,
            PhysicalUnit("pascal"),
        )
        self.assertIs(
            observation.stress_tensor.sign_convention,
            StressSignConvention.TENSION_POSITIVE,
        )
        self.assertTrue(
            np.all(np.diag(observation.stress_tensor.components.magnitude) < 0.0)
        )
        assert observation.pressure_kbar is not None
        self.assertAlmostEqual(
            observation.pressure_kbar,
            observation.stress_tensor.hydrostatic_pressure.magnitude / 1.0e8,
        )
        self.assertTrue(
            np.array_equal(
                observation.final_unit_cell.direct_lattice.A,
                starting_structure.unit_cell.direct_lattice.A,
            )
        )
        self.assertEqual(
            observation.final_unit_cell.lattice_parameter,
            starting_structure.unit_cell.lattice_parameter,
        )
        self.assertEqual(observation.program_version, "7.5")
        self.assertEqual(observation.ionic_step_count, 2)
        self.assertEqual(len(observation.native_artifacts), 3)

    def test__QeRelaxDataExtractor__does_not_manufacture_success_from_empty_stderr(
        self,
    ) -> None:
        data = _RELAX_DATA_EXTRACTOR.extract(
            stdout_payload=b"Program PWSCF v.7.5\n",
            stderr_payload=b"",
        )

        self.assertFalse(data.streams.stdout.job_completed)
        self.assertFalse(data.streams.stdout.geometry_optimization_converged)
        self.assertEqual(data.trajectory.steps, ())
        self.assertEqual(data.streams.stderr.ieee_flags, ())


if __name__ == "__main__":
    unittest.main()
