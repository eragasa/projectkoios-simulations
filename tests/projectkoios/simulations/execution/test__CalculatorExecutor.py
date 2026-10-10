from __future__ import annotations

import io
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from typing import BinaryIO
from unittest.mock import patch

import pytest

from projectkoios.simulations import execution as execution_module
from projectkoios.simulations.execution import (
    CalculatorExecutionError,
    CalculatorExecutionRequest,
    CalculatorExecutor,
    CalculatorOutputEmissionError,
    ExecutionStatus,
)

pytestmark = pytest.mark.integration


class CalculatorExecutorTest(unittest.TestCase):
    def test_rejects_execution_without_explicit_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            request = CalculatorExecutionRequest(
                command=(sys.executable, "-c", "raise SystemExit('must not run')"),
                working_directory=working_directory,
            )

            with self.assertRaisesRegex(PermissionError, "not authorized"):
                CalculatorExecutor().execute(request)

            self.assertFalse((working_directory / "stdout.txt").exists())
            self.assertFalse((working_directory / "execution.json").exists())

    def test_rejects_preflight_record_without_explicit_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            request = CalculatorExecutionRequest(
                command=("/must/not/run",),
                working_directory=working_directory,
            )

            with self.assertRaisesRegex(PermissionError, "not authorized"):
                CalculatorExecutor().record_preflight_failure(
                    request,
                    FileNotFoundError("missing input"),
                )

            self.assertFalse((working_directory / "execution.json").exists())
            self.assertEqual(tuple(working_directory.iterdir()), ())

    def test_records_success_before_returning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            record = CalculatorExecutor().execute(
                CalculatorExecutionRequest(
                    command=(sys.executable, "-c", "print('complete')"),
                    working_directory=working_directory,
                    execution_authorized=True,
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
                        execution_authorized=True,
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
                        execution_authorized=True,
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
                        execution_authorized=True,
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
                        execution_authorized=True,
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


def test_starts_exactly_one_process_for_one_request() -> None:
    real_popen = execution_module.subprocess.Popen
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)

        with patch.object(
            execution_module.subprocess,
            "Popen",
            side_effect=real_popen,
        ) as start:
            record = CalculatorExecutor().execute(
                CalculatorExecutionRequest(
                    command=(sys.executable, "-c", "pass"),
                    working_directory=working_directory,
                    execution_authorized=True,
                )
            )

        assert record.status is ExecutionStatus.succeeded
        assert start.call_count == 1


def test_tees_exact_binary_streams_to_console_and_artifacts(
    capfdbinary: pytest.CaptureFixture[bytes],
) -> None:
    stdout_payload = b"stdout\x00\xff-without-final-newline"
    stderr_payload = b"stderr\x00\xfe-without-final-newline"
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)

        record = CalculatorExecutor().execute(
            CalculatorExecutionRequest(
                command=(
                    sys.executable,
                    "-c",
                    (
                        "import sys; "
                        f"sys.stdout.buffer.write({stdout_payload!r}); "
                        "sys.stdout.buffer.flush(); "
                        f"sys.stderr.buffer.write({stderr_payload!r}); "
                        "sys.stderr.buffer.flush()"
                    ),
                ),
                working_directory=working_directory,
                execution_authorized=True,
            )
        )

        captured = capfdbinary.readouterr()
        assert record.status is ExecutionStatus.succeeded
        assert captured.out == stdout_payload
        assert captured.err == stderr_payload
        assert (working_directory / "stdout.txt").read_bytes() == stdout_payload
        assert (working_directory / "stderr.txt").read_bytes() == stderr_payload


def test_emits_first_chunk_before_process_completion() -> None:
    first = b"first-live-chunk"
    second = b"second-live-chunk"
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)
        acknowledgement = working_directory / "emitted"
        emitted: list[tuple[bytes, bool]] = []

        def observe_output(stream_name: str, chunk: bytes) -> None:
            assert stream_name == "stdout"
            emitted.append((chunk, acknowledgement.exists()))
            acknowledgement.touch()

        command = (
            "import pathlib, sys, time; "
            f"ack = pathlib.Path({str(acknowledgement)!r}); "
            f"sys.stdout.buffer.write({first!r}); sys.stdout.buffer.flush(); "
            "deadline = time.monotonic() + 5.0; "
            'exec("while not ack.exists():\\n'
            "    assert time.monotonic() < deadline\\n"
            '    time.sleep(0.01)"); '
            f"sys.stdout.buffer.write({second!r}); sys.stdout.buffer.flush()"
        )
        with patch.object(execution_module, "_emit_output", observe_output):
            record = CalculatorExecutor().execute(
                CalculatorExecutionRequest(
                    command=(sys.executable, "-c", command),
                    working_directory=working_directory,
                    timeout_seconds=10.0,
                    execution_authorized=True,
                )
            )

        assert record.status is ExecutionStatus.succeeded
        assert emitted[0] == (first, False)
        assert b"".join(chunk for chunk, _ in emitted) == first + second
        assert (working_directory / "stdout.txt").read_bytes() == first + second


def test_drains_large_stdout_and_stderr_without_pipe_deadlock(
    capfdbinary: pytest.CaptureFixture[bytes],
) -> None:
    byte_count = 512 * 1024
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)

        record = CalculatorExecutor().execute(
            CalculatorExecutionRequest(
                command=(
                    sys.executable,
                    "-c",
                    (
                        "import sys; "
                        f"sys.stdout.buffer.write(b'o' * {byte_count}); "
                        "sys.stdout.buffer.flush(); "
                        f"sys.stderr.buffer.write(b'e' * {byte_count}); "
                        "sys.stderr.buffer.flush()"
                    ),
                ),
                working_directory=working_directory,
                timeout_seconds=10.0,
                execution_authorized=True,
            )
        )

        captured = capfdbinary.readouterr()
        assert record.status is ExecutionStatus.succeeded
        assert captured.out == b"o" * byte_count
        assert captured.err == b"e" * byte_count
        assert (working_directory / "stdout.txt").read_bytes() == captured.out
        assert (working_directory / "stderr.txt").read_bytes() == captured.err


def test_retains_and_emits_partial_output_after_nonzero_exit(
    capfdbinary: pytest.CaptureFixture[bytes],
) -> None:
    payload = b"partial-before-failure\xff"
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)

        with pytest.raises(CalculatorExecutionError) as caught:
            CalculatorExecutor().execute(
                CalculatorExecutionRequest(
                    command=(
                        sys.executable,
                        "-c",
                        (
                            "import sys; "
                            f"sys.stdout.buffer.write({payload!r}); "
                            "sys.stdout.buffer.flush(); raise SystemExit(7)"
                        ),
                    ),
                    working_directory=working_directory,
                    execution_authorized=True,
                )
            )

        captured = capfdbinary.readouterr()
        assert caught.value.record.status is ExecutionStatus.failed
        assert caught.value.record.returncode == 7
        assert captured.out == payload
        assert (working_directory / "stdout.txt").read_bytes() == payload


def test_retains_and_emits_partial_output_after_timeout(
    capfdbinary: pytest.CaptureFixture[bytes],
) -> None:
    payload = b"partial-before-timeout\xff"
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)

        with pytest.raises(CalculatorExecutionError) as caught:
            CalculatorExecutor().execute(
                CalculatorExecutionRequest(
                    command=(
                        sys.executable,
                        "-c",
                        (
                            "import sys, time; "
                            f"sys.stdout.buffer.write({payload!r}); "
                            "sys.stdout.buffer.flush(); time.sleep(10)"
                        ),
                    ),
                    working_directory=working_directory,
                    timeout_seconds=0.5,
                    execution_authorized=True,
                )
            )

        captured = capfdbinary.readouterr()
        assert caught.value.record.status is ExecutionStatus.timed_out
        assert captured.out == payload
        assert (working_directory / "stdout.txt").read_bytes() == payload


def test_records_retained_output_failure_after_draining_process() -> None:
    payload = b"emitted-despite-retention-failure"
    real_write_and_flush = execution_module._write_and_flush
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)
        stdout_path = working_directory / "stdout.txt"

        def fail_stdout_capture(destination: BinaryIO, chunk: bytes) -> None:
            if getattr(destination, "name", None) == str(stdout_path):
                raise OSError("simulated retained-output failure")
            real_write_and_flush(destination, chunk)

        with (
            patch.object(
                execution_module,
                "_write_and_flush",
                fail_stdout_capture,
            ),
            pytest.raises(CalculatorExecutionError) as caught,
        ):
            CalculatorExecutor().execute(
                CalculatorExecutionRequest(
                    command=(
                        sys.executable,
                        "-c",
                        f"import sys; sys.stdout.buffer.write({payload!r})",
                    ),
                    working_directory=working_directory,
                    execution_authorized=True,
                )
            )

        assert caught.value.record.status is ExecutionStatus.failed_output
        assert caught.value.record.returncode == 0
        assert "stdout capture failed" in (caught.value.record.error_message or "")
        assert stdout_path.read_bytes() == b""
        on_disk = json.loads(caught.value.record_path.read_text(encoding="utf-8"))
        assert on_disk["status"] == "failed-output"


def test_reports_live_output_emission_failure_after_retaining_native_bytes() -> None:
    payload = b"retained-despite-console-failure"
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)

        with (
            patch.object(sys, "stdout", io.StringIO()),
            pytest.raises(CalculatorOutputEmissionError) as caught,
        ):
            CalculatorExecutor().execute(
                CalculatorExecutionRequest(
                    command=(
                        sys.executable,
                        "-c",
                        f"import sys; sys.stdout.buffer.write({payload!r})",
                    ),
                    working_directory=working_directory,
                    execution_authorized=True,
                )
            )

        assert caught.value.record.status is ExecutionStatus.succeeded
        assert caught.value.record.returncode == 0
        assert "stdout emission failed" in str(caught.value)
        assert (working_directory / "stdout.txt").read_bytes() == payload
        on_disk = json.loads(caught.value.record_path.read_text(encoding="utf-8"))
        assert on_disk["status"] == "succeeded"


@pytest.mark.parametrize("timeout", [math.nan, math.inf, -math.inf])
def test_rejects_nonfinite_timeout(timeout: float) -> None:
    with (
        tempfile.TemporaryDirectory() as temporary_directory,
        pytest.raises(ValueError, match="positive and finite"),
    ):
        CalculatorExecutionRequest(
            command=(sys.executable, "-c", "pass"),
            working_directory=Path(temporary_directory),
            timeout_seconds=timeout,
            execution_authorized=True,
        )


if __name__ == "__main__":
    unittest.main()
