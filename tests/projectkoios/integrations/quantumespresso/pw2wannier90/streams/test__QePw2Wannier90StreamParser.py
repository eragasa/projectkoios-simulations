from __future__ import annotations

import hashlib
import unittest

from projectkoios.integrations.quantumespresso.pw2wannier90.streams import (  # noqa: E501
    QePw2Wannier90StreamParser,
)


class QePw2Wannier90StreamParserTest(unittest.TestCase):
    def test_retains_native_completion_and_interface_observations(self) -> None:
        stdout = (
            b"Program PW2WANNIER v.7.5 starts on 1Jan2026\n"
            b" - Real lattice is ok\n"
            b" - Reciprocal lattice is ok\n"
            b" - K-points are ok\n"
            b" - Number of wannier functions is ok (  4)\n"
            b" - All guiding functions are given\n"
            b" All neighbours are found\n"
            b" AMN calculated\n"
            b" MMN calculated\n"
            b" JOB DONE.\n"
        )

        result = QePw2Wannier90StreamParser().parse(stdout, b"")

        self.assertEqual(result.program_version, "7.5")
        self.assertTrue(result.job_done)
        self.assertTrue(result.real_lattice_accepted)
        self.assertTrue(result.reciprocal_lattice_accepted)
        self.assertTrue(result.kpoints_accepted)
        self.assertEqual(result.wannier_function_count, 4)
        self.assertTrue(result.guiding_functions_complete)
        self.assertTrue(result.all_neighbors_found)
        self.assertTrue(result.amn_calculated)
        self.assertTrue(result.mmn_calculated)
        self.assertEqual(result.fatal_diagnostics, ())
        self.assertEqual(result.stdout_sha256, hashlib.sha256(stdout).hexdigest())

    def test_retains_fatal_diagnostics_despite_job_done_marker(self) -> None:
        result = QePw2Wannier90StreamParser().parse(
            b"Error in routine pw2wannier90 (1): bad input\nJOB DONE.\n",
            b"MPI_ABORT invoked\n",
        )

        self.assertTrue(result.job_done)
        self.assertEqual(
            result.fatal_diagnostics,
            (
                "Error in routine pw2wannier90 (1): bad input",
                "MPI_ABORT invoked",
            ),
        )


if __name__ == "__main__":
    unittest.main()
