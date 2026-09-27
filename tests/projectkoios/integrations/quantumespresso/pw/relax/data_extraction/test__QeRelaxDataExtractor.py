from __future__ import annotations

import hashlib
import unittest

from projectkoios.integrations.quantumespresso.pw.relax.data_extraction import (  # noqa: E501
    QeRelaxDataExtractor,
)

_STDOUT = b"""Program PWSCF v.7.5 starts on 1Jan2026
axis vectors are left-handed
energy new = -10.000900 Ry
bfgs converged in 3 scf cycles and 2 bfgs steps
(criteria: energy < 1.0E-04, force < 1.0E-03)
End of BFGS Geometry Optimization
Final energy = -10.001000 Ry
JOB DONE.
"""
_STDERR = b"IEEE_UNDERFLOW_FLAG\n"


class QeRelaxDataExtractorTest(unittest.TestCase):
    def test_extracts_fixed_cell_native_data(self) -> None:
        data = QeRelaxDataExtractor().extract(
            stdout_payload=_STDOUT,
            stderr_payload=_STDERR,
            stdout_relative_path="run/pw.out",
            stderr_relative_path="run/pw.err",
        )

        self.assertEqual(
            data.streams.stdout_artifact.sha256,
            hashlib.sha256(_STDOUT).hexdigest(),
        )
        self.assertTrue(data.streams.stdout.job_completed)
        self.assertTrue(data.streams.stdout.geometry_optimization_converged)
        self.assertTrue(data.streams.stdout.left_handed_axis_warning)
        self.assertAlmostEqual(data.streams.stdout.bfgs_energy_change_ry, 0.0001)
        self.assertEqual(
            data.streams.stderr.ieee_flags,
            ("IEEE_UNDERFLOW_FLAG",),
        )
        self.assertIsNone(data.final_structure)

    def test_does_not_manufacture_success_from_empty_stderr(self) -> None:
        data = QeRelaxDataExtractor().extract(
            stdout_payload=b"Program PWSCF v.7.5\n",
            stderr_payload=b"",
        )

        self.assertFalse(data.streams.stdout.job_completed)
        self.assertFalse(data.streams.stdout.geometry_optimization_converged)
        self.assertEqual(data.streams.stderr.ieee_flags, ())


if __name__ == "__main__":
    unittest.main()
