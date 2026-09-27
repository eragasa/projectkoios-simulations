from __future__ import annotations

import hashlib
import unittest

from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (  # noqa: E501
    QePwCapturedStreamDataExtractor,
    QePwNativeArtifact,
)


class QePwCapturedStreamDataExtractorTest(unittest.TestCase):
    def test_binds_exact_stream_identities_to_parsed_data(self) -> None:
        stdout = b"Program PWSCF v.7.5\nJOB DONE.\n"
        stderr = b"IEEE_UNDERFLOW_FLAG\n"

        data = QePwCapturedStreamDataExtractor().extract(
            stdout_payload=stdout,
            stderr_payload=stderr,
            stdout_relative_path="run/pw.out",
            stderr_relative_path="run/pw.err",
        )

        self.assertEqual(
            data.stdout_artifact.sha256,
            hashlib.sha256(stdout).hexdigest(),
        )
        self.assertEqual(
            data.stderr_artifact.sha256,
            hashlib.sha256(stderr).hexdigest(),
        )
        self.assertTrue(data.stdout.job_completed)
        self.assertEqual(data.stderr.ieee_flags, ("IEEE_UNDERFLOW_FLAG",))

    def test_native_artifact_rejects_unsafe_relative_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "safe relative POSIX path"):
            QePwNativeArtifact(
                relative_path="../pw.out",
                sha256="0" * 64,
                byte_size=1,
            )


if __name__ == "__main__":
    unittest.main()
