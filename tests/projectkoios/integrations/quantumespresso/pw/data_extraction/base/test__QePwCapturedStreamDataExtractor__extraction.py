from __future__ import annotations

import hashlib
import unittest

from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (  # noqa: E501
    QePwCapturedStreamDataExtractor,
    QePwDataSources,
    QePwNativeArtifact,
)
from projectkoios.simulations.execution import (
    CalculatorExecutionRecord,
    ExecutionStatus,
)


class QePwCapturedStreamDataExtractorTest(unittest.TestCase):
    def test__QePwCapturedStreamDataExtractor__binds_exact_stream_identities(
        self,
    ) -> None:
        stdout = b"Program PWSCF v.7.5\nJOB DONE.\n"
        stderr = b"IEEE_UNDERFLOW_FLAG\n"

        data = QePwCapturedStreamDataExtractor(
            stdout_relative_path="run/pw.out",
            stderr_relative_path="run/pw.err",
        ).extract(
            stdout_payload=stdout,
            stderr_payload=stderr,
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

    def test__QePwCapturedStreamDataExtractor__rejects_unsafe_execution_filenames(
        self,
    ) -> None:
        streams = QePwCapturedStreamDataExtractor(
            stdout_relative_path="pw.out",
            stderr_relative_path="pw.err",
        ).extract(
            stdout_payload=b"Program PWSCF v.7.5\nJOB DONE.\n",
            stderr_payload=b"",
        )
        execution = CalculatorExecutionRecord(
            command=("pw.x",),
            working_directory="/tmp/run",
            status=ExecutionStatus.succeeded,
            returncode=0,
            stdout_filename="../pw.out",
            stderr_filename="pw.err",
            required_input_filenames=(),
        )

        with self.assertRaisesRegex(ValueError, "basename"):
            QePwDataSources(streams=streams, execution=execution)

    def test__QePwCapturedStreamDataExtractor__rejects_unsafe_relative_path(
        self,
    ) -> None:
        with self.assertRaisesRegex(ValueError, "safe relative POSIX path"):
            QePwNativeArtifact(
                relative_path="../pw.out",
                sha256="0" * 64,
                byte_size=1,
            )


if __name__ == "__main__":
    unittest.main()
