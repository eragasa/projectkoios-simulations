from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.pw.vc_relax.data_extraction import (  # noqa: E501
    QeVcRelaxDataExtractor,
)


class QeVcRelaxDataExtractorTest(unittest.TestCase):
    def test_extracts_variable_cell_native_data(self) -> None:
        data = QeVcRelaxDataExtractor().extract(
            stdout_payload=(
                b"Program PWSCF v.7.5\n"
                b"enthalpy new = -10.000900 Ry\n"
                b"bfgs converged in 4 scf cycles and 3 bfgs steps\n"
                b"(criteria: energy < 1.0E-04, force < 1.0E-03, cell < 5.0E-01)\n"
                b"End of BFGS Geometry Optimization\n"
                b"Final enthalpy = -10.001000 Ry\n"
                b"JOB DONE.\n"
            ),
            stderr_payload=b"",
        )

        self.assertTrue(data.streams.stdout.job_completed)
        self.assertTrue(data.streams.stdout.geometry_optimization_converged)
        self.assertEqual(data.streams.stdout.bfgs_objective_kind, "enthalpy")
        self.assertAlmostEqual(data.streams.stdout.bfgs_cell_threshold_kbar or 0.0, 0.5)
        self.assertIsNone(data.final_structure)


if __name__ == "__main__":
    unittest.main()
