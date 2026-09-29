from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.outputs.pw_stdout import (
    QePwStdoutFile,
    QePwStdoutFileParser,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.trajectory import (
    QeRelaxationTrajectoryParser,
)

_RELAX_OUTPUT = b"""Program PWSCF v.7.5 starts on 1Jan2026
! total energy = -10.000000D+00 Ry
convergence has been achieved in 5 iterations
Forces acting on atoms (Cartesian axes, Ry/au):
atom 1 type 1 force = 0.100000 0.000000 0.000000
atom 2 type 1 force = -0.100000 0.000000 0.000000
Total force = 0.141421 Total SCF correction = 0.000002
number of scf cycles = 1
number of bfgs steps = 0
energy new = -10.000000D+00 Ry
ATOMIC_POSITIONS (alat)
Si 0.010000 0.000000 0.000000 1 1 1
Si 0.240000 0.250000 0.250000 1 1 0
! total energy = -10.100000 Ry
convergence has been achieved in 3 iterations
atom 1 type 1 force = 0.001000 0.000000 0.000000
atom 2 type 1 force = -0.001000 0.000000 0.000000
Total force = 0.001414 Total SCF correction = 0.000001
bfgs converged in 2 scf cycles and 1 bfgs steps
End of BFGS Geometry Optimization
Final energy = -10.100000 Ry
Begin final coordinates
ATOMIC_POSITIONS (alat)
Si 0.011000 0.000000 0.000000
Si 0.239000 0.250000 0.250000
End final coordinates
JOB DONE.
"""

_VC_RELAX_OUTPUT = b"""Program PWSCF v.7.5 starts on 1Jan2026
! total energy = -20.000000 Ry
convergence has been achieved in 4 iterations
atom 1 type 1 force = 0.000000 0.000000 0.010000
atom 2 type 1 force = 0.000000 0.000000 -0.010000
Total force = 0.014142 Total SCF correction = 0.000003
total stress (Ry/bohr**3) (kbar) P= 1.25
0.000001 0.000002 0.000003 0.1 0.2 0.3
0.000004 0.000005 0.000006 0.4 0.5 0.6
0.000007 0.000008 0.000009 0.7 0.8 0.9
enthalpy new = -19.999000 Ry
CELL_PARAMETERS (alat= 10.20)
1.000000 0.000000 0.000000
0.000000 1.010000 0.000000
0.000000 0.000000 0.990000
ATOMIC_POSITIONS (crystal)
Si 0.000000 0.000000 0.000000
Si 0.250000 0.250000 0.250000
JOB DONE.
"""


def _summary(payload: bytes):  # type: ignore[no-untyped-def]
    return QePwStdoutFileParser().parse(
        payload,
        output_file=QePwStdoutFile.from_prefix(prefix="silicon"),
    )


class QeRelaxationTrajectoryParserTest(unittest.TestCase):
    def test_retains_every_fixed_cell_evaluation_and_emitted_position_block(
        self,
    ) -> None:
        trajectory = QeRelaxationTrajectoryParser().parse(
            _RELAX_OUTPUT,
            calculation="relax",
            summary=_summary(_RELAX_OUTPUT),
        )

        self.assertEqual(trajectory.calculation, "relax")
        self.assertEqual(len(trajectory.steps), 2)

        first = trajectory.steps[0]
        self.assertEqual(first.sequence_index, 1)
        self.assertEqual(first.total_energy_ry, -10.0)
        self.assertTrue(first.scf_converged)
        self.assertEqual(first.scf_iteration_count, 5)
        self.assertEqual(len(first.atomic_forces), 2)
        self.assertEqual(first.atomic_forces[0].atom_index, 1)
        self.assertEqual(first.atomic_forces[0].force_ry_per_bohr, (0.1, 0.0, 0.0))
        self.assertEqual(first.total_force_ry_per_bohr, 0.141421)
        self.assertEqual(first.total_scf_correction_ry_per_bohr, 0.000002)
        self.assertEqual(first.optimizer_scf_cycle_count, 1)
        self.assertEqual(first.optimizer_step_count, 0)
        self.assertEqual(first.objective_kind, "energy")
        self.assertEqual(first.new_objective_ry, -10.0)
        self.assertIsNone(first.emitted_cell)
        self.assertIsNotNone(first.emitted_positions)
        assert first.emitted_positions is not None
        self.assertEqual(first.emitted_positions.source_label, "alat")
        self.assertFalse(first.emitted_positions.final_coordinates)
        self.assertEqual(first.emitted_positions.atoms[1].movement_mask, (1, 1, 0))

        final = trajectory.steps[1]
        self.assertEqual(final.total_energy_ry, -10.1)
        self.assertEqual(final.scf_iteration_count, 3)
        self.assertIsNotNone(final.emitted_positions)
        assert final.emitted_positions is not None
        self.assertTrue(final.emitted_positions.final_coordinates)
        self.assertEqual(
            final.emitted_positions.atoms[0].coordinates, (0.011, 0.0, 0.0)
        )

    def test_retains_variable_cell_stress_cell_and_positions(self) -> None:
        trajectory = QeRelaxationTrajectoryParser().parse(
            _VC_RELAX_OUTPUT,
            calculation="vc-relax",
            summary=_summary(_VC_RELAX_OUTPUT),
        )

        self.assertEqual(len(trajectory.steps), 1)
        step = trajectory.steps[0]
        self.assertEqual(step.pressure_kbar, 1.25)
        self.assertEqual(
            step.stress_ry_per_bohr_cubed,
            (
                (0.000001, 0.000002, 0.000003),
                (0.000004, 0.000005, 0.000006),
                (0.000007, 0.000008, 0.000009),
            ),
        )
        self.assertEqual(step.objective_kind, "enthalpy")
        self.assertEqual(step.new_objective_ry, -19.999)
        self.assertIsNotNone(step.emitted_cell)
        assert step.emitted_cell is not None
        self.assertEqual(step.emitted_cell.source_label, "alat= 10.20")
        self.assertEqual(step.emitted_cell.vectors[1], (0.0, 1.01, 0.0))
        self.assertIsNotNone(step.emitted_positions)
        assert step.emitted_positions is not None
        self.assertEqual(step.emitted_positions.source_label, "crystal")
        self.assertEqual(len(step.emitted_positions.atoms), 2)

    def test_retains_empty_trajectory_for_failure_before_first_evaluation(self) -> None:
        payload = b"Program PWSCF v.7.5 starts on 1Jan2026\n"
        trajectory = QeRelaxationTrajectoryParser().parse(
            payload,
            calculation="relax",
            summary=_summary(payload),
        )

        self.assertEqual(trajectory.steps, ())
        self.assertFalse(trajectory.summary.job_completed)

    def test_rejects_cell_trajectory_for_fixed_cell_mode(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "relax trajectory must not contain emitted cell blocks",
        ):
            QeRelaxationTrajectoryParser().parse(
                _VC_RELAX_OUTPUT,
                calculation="relax",
                summary=_summary(_VC_RELAX_OUTPUT),
            )


if __name__ == "__main__":
    unittest.main()
