from __future__ import annotations

import hashlib
import unittest

from projectkoios.integrations.quantumespresso.epw.streams import QeEpwStreamParser


class QeEpwStreamParserTest(unittest.TestCase):
    def test_observes_native_completion_and_stage_markers(self) -> None:
        stdout = (
            b"Program EPW v.5.9 starts\n"
            b"Wannierization on 4 x 4 x 4 electronic grid\n"
            b"Electron-Phonon interpolation\n"
            b"Total program execution\n"
            b"EPW : 1.0s CPU 1.1s WALL\n"
            b"JOB DONE.\n"
        )
        stderr = b""

        observed = QeEpwStreamParser().parse(stdout, stderr)

        self.assertEqual(observed.program_version, "5.9")
        self.assertTrue(observed.job_done)
        self.assertTrue(observed.total_program_execution_reported)
        self.assertTrue(observed.wannierization_reported)
        self.assertTrue(observed.electron_phonon_interpolation_reported)
        self.assertEqual(observed.fatal_diagnostics, ())
        self.assertEqual(observed.stdout_sha256, hashlib.sha256(stdout).hexdigest())

    def test_retains_fatal_diagnostics_without_deciding_acceptance(self) -> None:
        observed = QeEpwStreamParser().parse(
            b"Program EPW v.5.9 starts\n",
            b"Error in routine readin: malformed input\nMPI_ABORT invoked\n",
        )

        self.assertFalse(observed.job_done)
        self.assertEqual(len(observed.fatal_diagnostics), 2)

    def test_rejects_nonbyte_payloads(self) -> None:
        with self.assertRaisesRegex(TypeError, "bytes"):
            QeEpwStreamParser().parse("not bytes", b"")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
