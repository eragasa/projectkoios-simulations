from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.outputs.base import (
    QeOutputFileParser,
    QeOutputFileResult,
    QuantumEspressoOutputFileError,
)
from projectkoios.integrations.quantumespresso.outputs.pw_stdout import (
    QePwStdoutFile,
    QePwStdoutFileParser,
)

PW_OUTPUT = b"""Program PWSCF v.7.2 starts on  1Jan2026
     number of atoms/cell      =            2
     number of k points=    29
     kinetic-energy cutoff     =      40.0000  Ry
     iteration #  1     ecut=    40.00 Ry
     iteration #  2     ecut=    40.00 Ry
     convergence has been achieved in   2 iterations
!    total energy              =     -15.12300000 Ry
          total   stress  (Ry/bohr**3)                   (kbar)     P=       -0.12
!    total energy              =     -15.12456789 Ry
JOB DONE.
"""

RELAX_OUTPUT = b"""Program PWSCF v.7.5 starts on  1Jan2026
     convergence has been achieved in 4 iterations
     Forces acting on atoms (Cartesian axes, Ry/au):
     atom 1 type 1 force = 0.00003000 -0.00004000 0.00000000
     atom 2 type 1 force = -0.00003000 0.00004000 0.00000000
     Total force = 0.000080 Total SCF correction = 0.000002
          total   stress  (Ry/bohr**3) (kbar) P= 0.20
  0.00000100  0.00000000  0.00000000  0.10 0.00 0.00
  0.00000000  0.00000200  0.00000000  0.00 0.20 0.00
  0.00000000  0.00000000  0.00000300  0.00 0.00 0.30
     enthalpy new = -22.799950D+00 Ry
     bfgs converged in  7 scf cycles and  6 bfgs steps
     (criteria: energy < 1.0E-04, force < 1.0E-03, cell < 5.0E-01)
     End of BFGS Geometry Optimization
     Final enthalpy = -22.800000D+00 Ry
     convergence has been achieved in 3 iterations
     Forces acting on atoms (Cartesian axes, Ry/au):
     atom 1 type 1 force = 0.00000000 0.00000000 0.00006000
     atom 2 type 1 force = 0.00000000 0.00000000 -0.00006000
     Total force = 0.000090 Total SCF correction = 0.000001
          total   stress  (Ry/bohr**3) (kbar) P= 0.35
  0.00000400  0.00000000  0.00000000  0.40 0.00 0.00
  0.00000000  0.00000500  0.00000000  0.00 0.50 0.00
  0.00000000  0.00000000  0.00000600  0.00 0.00 0.60
JOB DONE.
"""


class QePwStdoutFileParserTest(unittest.TestCase):
    def test_parse_uses_native_units_and_last_energy(self) -> None:
        parser = QePwStdoutFileParser()
        output = parser.parse(
            PW_OUTPUT,
            output_file=QePwStdoutFile.from_prefix(prefix="silicon"),
        )

        self.assertIsInstance(parser, QeOutputFileParser)
        self.assertIsInstance(output, QeOutputFileResult)
        self.assertEqual(output.program_version, "7.2")
        self.assertTrue(output.job_completed)
        self.assertTrue(output.scf_converged)
        self.assertEqual(output.total_energy_ry, -15.12456789)
        self.assertEqual(output.wavefunction_cutoff_ry, 40.0)
        self.assertEqual(output.pressure_kbar, -0.12)
        self.assertEqual(output.atom_count, 2)
        self.assertEqual(output.k_point_count, 29)
        self.assertEqual(output.scf_iteration_count, 2)

    def test_parse_retains_optimizer_and_post_relaxation_observations(self) -> None:
        output = QePwStdoutFileParser().parse(
            RELAX_OUTPUT,
            output_file=QePwStdoutFile.from_prefix(prefix="silicon"),
        )

        self.assertTrue(output.geometry_optimization_converged)
        self.assertEqual(output.bfgs_scf_cycle_count, 7)
        self.assertEqual(output.bfgs_step_count, 6)
        self.assertEqual(output.bfgs_energy_threshold_ry, 1.0e-4)
        self.assertEqual(output.bfgs_force_threshold_ry_per_bohr, 1.0e-3)
        self.assertEqual(output.bfgs_cell_threshold_kbar, 0.5)
        self.assertEqual(output.optimizer_total_force_ry_per_bohr, 0.000080)
        self.assertEqual(output.optimizer_maximum_atomic_force_ry_per_bohr, 0.00005)
        self.assertEqual(
            output.optimizer_maximum_force_component_ry_per_bohr,
            0.00004,
        )
        self.assertEqual(output.optimizer_pressure_kbar, 0.20)
        self.assertEqual(
            output.optimizer_stress_ry_per_bohr_cubed,
            (
                (0.000001, 0.0, 0.0),
                (0.0, 0.000002, 0.0),
                (0.0, 0.0, 0.000003),
            ),
        )
        self.assertEqual(output.total_force_ry_per_bohr, 0.000090)
        self.assertEqual(output.total_scf_correction_ry_per_bohr, 0.000001)
        self.assertEqual(output.maximum_atomic_force_ry_per_bohr, 0.00006)
        self.assertEqual(output.maximum_force_component_ry_per_bohr, 0.00006)
        self.assertEqual(output.pressure_kbar, 0.35)
        self.assertEqual(
            output.stress_ry_per_bohr_cubed,
            (
                (0.000004, 0.0, 0.0),
                (0.0, 0.000005, 0.0),
                (0.0, 0.0, 0.000006),
            ),
        )
        self.assertEqual(output.bfgs_objective_kind, "enthalpy")
        self.assertEqual(output.previous_bfgs_objective_ry, -22.79995)
        self.assertEqual(output.final_bfgs_objective_ry, -22.8)
        self.assertAlmostEqual(output.bfgs_energy_change_ry, 0.00005)
        self.assertEqual(output.final_enthalpy_ry, -22.8)
        self.assertIsNone(output.final_energy_ry)
        self.assertEqual(output.scf_nonconvergence_count, 0)

    def test_parse_fixed_cell_bfgs_energy_change(self) -> None:
        output = QePwStdoutFileParser().parse(
            b"energy new = -10.000900 Ry\n"
            b"bfgs converged in 3 scf cycles and 2 bfgs steps\n"
            b"End of BFGS Geometry Optimization\n"
            b"Final energy = -10.001000 Ry\n",
            output_file=QePwStdoutFile.from_prefix(prefix="silicon"),
        )

        self.assertEqual(output.bfgs_objective_kind, "energy")
        self.assertAlmostEqual(output.bfgs_energy_change_ry, 0.0001)
        self.assertEqual(output.final_energy_ry, -10.001)
        self.assertIsNone(output.final_enthalpy_ry)

    def test_parse_counts_native_scf_nonconvergence(self) -> None:
        output = QePwStdoutFileParser().parse(
            b"convergence NOT achieved after 100 iterations\n",
            output_file=QePwStdoutFile.from_prefix(prefix="silicon"),
        )

        self.assertFalse(output.scf_converged)
        self.assertEqual(output.scf_nonconvergence_count, 1)

    def test_parse_retains_left_handed_warning_as_observation(self) -> None:
        output = QePwStdoutFileParser().parse(
            b"axis vectors are left-handed\nJOB DONE.\n",
            output_file=QePwStdoutFile.from_prefix(prefix="silicon"),
        )

        self.assertTrue(output.left_handed_axis_warning)
        self.assertTrue(output.job_completed)

    def test_parse_retains_collinear_magnetization_in_native_units(self) -> None:
        output = QePwStdoutFileParser().parse(
            b"     total magnetization       =     -0.74 Bohr mag/cell\n"
            b"     absolute magnetization    =      0.83 Bohr mag/cell\n"
            b"JOB DONE.\n",
            output_file=QePwStdoutFile.from_prefix(prefix="nickel"),
        )

        self.assertEqual(
            output.total_magnetization_bohr_magneton_per_cell,
            -0.74,
        )
        self.assertEqual(
            output.absolute_magnetization_bohr_magneton_per_cell,
            0.83,
        )

    def test_parse_accepts_fortran_double_exponents(self) -> None:
        output = QePwStdoutFileParser().parse(
            b"! total energy = -1.234500D+01 Ry\nJOB DONE.\n",
            output_file=QePwStdoutFile.from_prefix(prefix="silicon"),
        )

        self.assertEqual(output.total_energy_ry, -12.345)
        self.assertTrue(output.job_completed)

    def test_parse_rejects_unrecognized_text(self) -> None:
        with self.assertRaisesRegex(
            QuantumEspressoOutputFileError,
            "no supported pw.x stdout observations",
        ):
            QePwStdoutFileParser().parse(
                b"not calculator output\n",
                output_file=QePwStdoutFile.from_prefix(prefix="silicon"),
            )


if __name__ == "__main__":
    unittest.main()
