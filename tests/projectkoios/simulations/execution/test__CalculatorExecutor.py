from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from projectkoios.simulations.execution import (
    CalculatorExecutionError,
    CalculatorExecutionRequest,
    CalculatorExecutor,
    ExecutionStatus,
)

pytestmark = pytest.mark.integration


class CalculatorExecutorTest(unittest.TestCase):
    def test_records_success_before_returning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            record = CalculatorExecutor().execute(
                CalculatorExecutionRequest(
                    command=(sys.executable, "-c", "print('complete')"),
                    working_directory=working_directory,
                )
            )

            self.assertIs(record.status, ExecutionStatus.succeeded)
            self.assertEqual(record.returncode, 0)
            self.assertEqual(
                (working_directory / "stdout.txt").read_text(encoding="utf-8"),
                "complete\n",
            )
            self.assertEqual(
                json.loads(
                    (working_directory / "execution.json").read_text(encoding="utf-8")
                )["status"],
                "succeeded",
            )

    def test_records_missing_required_input_before_starting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            marker = working_directory / "started"

            with self.assertRaises(CalculatorExecutionError) as caught:
                CalculatorExecutor().execute(
                    CalculatorExecutionRequest(
                        command=(
                            sys.executable,
                            "-c",
                            f"from pathlib import Path; Path({str(marker)!r}).touch()",
                        ),
                        working_directory=working_directory,
                        required_input_filenames=("Si.upf",),
                    )
                )

            self.assertIs(
                caught.exception.record.status,
                ExecutionStatus.failed_preflight,
            )
            self.assertFalse(marker.exists())
            on_disk = json.loads(
                caught.exception.record_path.read_text(encoding="utf-8")
            )
            self.assertEqual(on_disk["status"], "failed-preflight")
            self.assertIn("Si.upf", on_disk["error_message"])

    def test_records_nonzero_exit_before_raising(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)

            with self.assertRaises(CalculatorExecutionError) as caught:
                CalculatorExecutor().execute(
                    CalculatorExecutionRequest(
                        command=(
                            sys.executable,
                            "-c",
                            "import sys; print('bad'); sys.exit(7)",
                        ),
                        working_directory=working_directory,
                    )
                )

            self.assertIs(caught.exception.record.status, ExecutionStatus.failed)
            self.assertEqual(caught.exception.record.returncode, 7)
            on_disk = json.loads(
                caught.exception.record_path.read_text(encoding="utf-8")
            )
            self.assertEqual(on_disk["status"], "failed")
            self.assertEqual(on_disk["returncode"], 7)

    def test_records_timeout_before_raising(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)

            with self.assertRaises(CalculatorExecutionError) as caught:
                CalculatorExecutor().execute(
                    CalculatorExecutionRequest(
                        command=(
                            sys.executable,
                            "-c",
                            "import time; time.sleep(2)",
                        ),
                        working_directory=working_directory,
                        timeout_seconds=0.05,
                    )
                )

            self.assertIs(caught.exception.record.status, ExecutionStatus.timed_out)
            self.assertEqual(
                json.loads(caught.exception.record_path.read_text(encoding="utf-8"))[
                    "status"
                ],
                "timed-out",
            )

    def test_records_start_failure_before_raising(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)

            with self.assertRaises(CalculatorExecutionError) as caught:
                CalculatorExecutor().execute(
                    CalculatorExecutionRequest(
                        command=("/definitely/not/a/calculator",),
                        working_directory=working_directory,
                    )
                )

            self.assertIs(
                caught.exception.record.status,
                ExecutionStatus.failed_to_start,
            )
            self.assertEqual(
                json.loads(caught.exception.record_path.read_text(encoding="utf-8"))[
                    "status"
                ],
                "failed-to-start",
            )


if __name__ == "__main__":
    unittest.main()
