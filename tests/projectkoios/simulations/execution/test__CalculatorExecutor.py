from __future__ import annotations

import ast
import contextlib
import io
import json
import math
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from typing import BinaryIO
from unittest.mock import Mock, call, patch

import pytest

from projectkoios.physkit.core.actions import DataObjectActionizer
from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.core.results import ResultsObject
from projectkoios.simulations import execution as execution_module
from projectkoios.simulations.execution import (
    CalculatorExecutionError,
    CalculatorExecutionRecord,
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
                CalculatorExecutor().action(request=request)

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
                    request=request,
                    error=FileNotFoundError("missing input"),
                )

            self.assertFalse((working_directory / "execution.json").exists())
            self.assertEqual(tuple(working_directory.iterdir()), ())

    def test_records_success_before_returning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            record = CalculatorExecutor().action(
                request=CalculatorExecutionRequest(
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
                CalculatorExecutor().action(
                    request=CalculatorExecutionRequest(
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
                CalculatorExecutor().action(
                    request=CalculatorExecutionRequest(
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
                CalculatorExecutor().action(
                    request=CalculatorExecutionRequest(
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
                CalculatorExecutor().action(
                    request=CalculatorExecutionRequest(
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


def test_execution_contract_uses_data_objects_and_an_actionizer() -> None:
    request = CalculatorExecutionRequest(
        command=(sys.executable, "-c", "pass"),
        working_directory=Path.cwd(),
    )
    actionizer: DataObjectActionizer[
        CalculatorExecutionRequest,
        CalculatorExecutionRecord,
    ] = CalculatorExecutor()
    record = CalculatorExecutionRecord(
        command=request.command,
        working_directory=str(request.working_directory),
        status=ExecutionStatus.succeeded,
        returncode=0,
        stdout_filename=request.stdout_filename,
        stderr_filename=request.stderr_filename,
        required_input_filenames=request.required_input_filenames,
    )

    assert isinstance(request, DataObject)
    assert isinstance(record, ResultsObject)
    assert isinstance(actionizer, CalculatorExecutor)


def test_execution_module_uses_actionizer_methods_not_dangling_functions() -> None:
    module_path = Path(execution_module.__file__)
    syntax = ast.parse(module_path.read_text(encoding="utf-8"))

    assert not any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for node in syntax.body
    )
    for node in syntax.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for member in node.body:
            if not isinstance(member, ast.FunctionDef):
                continue
            decorator_names = {
                decorator.id
                for decorator in member.decorator_list
                if isinstance(decorator, ast.Name)
            }
            assert "staticmethod" not in decorator_names
            assert "classmethod" not in decorator_names


def test_starts_exactly_one_process_for_one_request() -> None:
    real_popen = execution_module.subprocess.Popen
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)

        with patch.object(
            execution_module.subprocess,
            "Popen",
            side_effect=real_popen,
        ) as start:
            record = CalculatorExecutor().action(
                request=CalculatorExecutionRequest(
                    command=(sys.executable, "-c", "pass"),
                    working_directory=working_directory,
                    execution_authorized=True,
                )
            )

        assert record.status is ExecutionStatus.succeeded
        assert start.call_count == 1
        assert start.call_args.kwargs["start_new_session"] is True


def test_second_stream_pump_start_failure_is_recorded_after_cleanup() -> None:
    real_start = threading.Thread.start
    started: list[threading.Thread] = []

    def fail_second_start(thread: threading.Thread) -> None:
        if started:
            raise RuntimeError("simulated second stream-pump start failure")
        started.append(thread)
        real_start(thread)

    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)
        with (
            patch.object(threading.Thread, "start", fail_second_start),
            pytest.raises(CalculatorExecutionError) as caught,
        ):
            CalculatorExecutor().action(
                request=CalculatorExecutionRequest(
                    command=(sys.executable, "-c", "import time; time.sleep(30)"),
                    working_directory=working_directory,
                    timeout_seconds=10.0,
                    execution_authorized=True,
                )
            )

        assert caught.value.record.status is ExecutionStatus.failed_output
        assert caught.value.record.returncode is not None
        assert caught.value.record.returncode != 0
        assert caught.value.record.error_type == "RuntimeError"
        assert "simulated second stream-pump start failure" in (
            caught.value.record.error_message or ""
        )
        assert len(started) == 1
        assert not started[0].is_alive()
        on_disk = json.loads(caught.value.record_path.read_text(encoding="utf-8"))
        assert on_disk["status"] == "failed-output"
        assert on_disk["error_type"] == "RuntimeError"


def test_tees_exact_binary_streams_to_console_and_artifacts(
    capfdbinary: pytest.CaptureFixture[bytes],
) -> None:
    stdout_payload = b"stdout\x00\xff-without-final-newline"
    stderr_payload = b"stderr\x00\xfe-without-final-newline"
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)

        record = CalculatorExecutor().action(
            request=CalculatorExecutionRequest(
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

        def observe_output(
            _executor: CalculatorExecutor,
            stream_name: str,
            chunk: bytes,
        ) -> None:
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
        with patch.object(CalculatorExecutor, "_emit_output", observe_output):
            record = CalculatorExecutor().action(
                request=CalculatorExecutionRequest(
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

        record = CalculatorExecutor().action(
            request=CalculatorExecutionRequest(
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


def test_stream_finish_preserves_parent_sink_backpressure() -> None:
    read_descriptor, write_descriptor = os.pipe()
    emission_started = threading.Event()
    emission_release = threading.Event()
    failures: list[execution_module._StreamPumpFailure] = []

    def emit_with_backpressure(_name: str, _chunk: bytes) -> None:
        emission_started.set()
        assert emission_release.wait(timeout=5.0)

    with (
        os.fdopen(read_descriptor, "rb", buffering=0) as source,
        tempfile.NamedTemporaryFile(mode="wb") as destination,
        patch.object(
            CalculatorExecutor,
            "_emit_output",
            side_effect=emit_with_backpressure,
        ),
    ):
        executor = CalculatorExecutor()
        pump = executor._start_stream_pump(
            name="stdout",
            source=source,
            destination=destination,
            failures=failures,
        )
        os.write(write_descriptor, b"backpressure")
        os.close(write_descriptor)
        finish = threading.Thread(
            target=executor._finish_stream_pumps,
            args=((pump,),),
        )
        finish.start()
        assert emission_started.wait(timeout=5.0)
        assert finish.is_alive()
        emission_release.set()
        finish.join(timeout=5.0)

    assert not finish.is_alive()
    assert failures == []


def test_retains_and_emits_partial_output_after_nonzero_exit(
    capfdbinary: pytest.CaptureFixture[bytes],
) -> None:
    payload = b"partial-before-failure\xff"
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)

        with pytest.raises(CalculatorExecutionError) as caught:
            CalculatorExecutor().action(
                request=CalculatorExecutionRequest(
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
            CalculatorExecutor().action(
                request=CalculatorExecutionRequest(
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


@pytest.mark.skipif(os.name != "posix", reason="requires POSIX process groups")
def test_timeout_terminates_descendant_process_group() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)
        descendant_pid_path = working_directory / "descendant.pid"
        descendant_code = (
            "import signal, time; "
            "signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)"
        )
        parent_code = (
            "import pathlib, signal, subprocess, sys, time; "
            "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
            f"child = subprocess.Popen([sys.executable, '-c', {descendant_code!r}]); "
            f"pathlib.Path({str(descendant_pid_path)!r}).write_text("
            "str(child.pid), encoding='utf-8'); "
            "print('descendant-started', flush=True); time.sleep(30)"
        )

        with pytest.raises(CalculatorExecutionError) as caught:
            CalculatorExecutor().action(
                request=CalculatorExecutionRequest(
                    command=(sys.executable, "-c", parent_code),
                    working_directory=working_directory,
                    timeout_seconds=0.75,
                    execution_authorized=True,
                )
            )

        assert caught.value.record.status is ExecutionStatus.timed_out
        descendant_pid = int(descendant_pid_path.read_text(encoding="utf-8"))
        deadline = time.monotonic() + 2.0
        while _process_exists(descendant_pid) and time.monotonic() < deadline:
            time.sleep(0.01)
        assert not _process_exists(descendant_pid)


def test_group_signal_failure_is_not_recorded_as_start_failure() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)

        with (
            patch.object(
                CalculatorExecutor,
                "_signal_process_group",
                side_effect=PermissionError("simulated group signal failure"),
            ),
            pytest.raises(CalculatorExecutionError) as caught,
        ):
            CalculatorExecutor().action(
                request=CalculatorExecutionRequest(
                    command=(sys.executable, "-c", "import time; time.sleep(30)"),
                    working_directory=working_directory,
                    timeout_seconds=0.25,
                    execution_authorized=True,
                )
            )

        assert caught.value.record.status is ExecutionStatus.failed_to_terminate
        assert "simulated group signal failure" in (
            caught.value.record.error_message or ""
        )
        on_disk = json.loads(caught.value.record_path.read_text(encoding="utf-8"))
        assert on_disk["status"] == "failed-to-terminate"


@pytest.mark.skipif(os.name != "posix", reason="requires POSIX process groups")
def test_termination_failure_aborts_reads_from_surviving_descendant() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)
        descendant_pid_path = working_directory / "escaped-descendant.pid"
        descendant_code = "import time; time.sleep(30)"
        parent_code = (
            "import pathlib, subprocess, sys, time; "
            f"child = subprocess.Popen([sys.executable, '-c', {descendant_code!r}], "
            "start_new_session=True); "
            f"pathlib.Path({str(descendant_pid_path)!r}).write_text("
            "str(child.pid), encoding='utf-8'); "
            "time.sleep(30)"
        )
        errors: list[CalculatorExecutionError] = []

        def invoke() -> None:
            try:
                CalculatorExecutor().action(
                    request=CalculatorExecutionRequest(
                        command=(sys.executable, "-c", parent_code),
                        working_directory=working_directory,
                        timeout_seconds=0.5,
                        execution_authorized=True,
                    )
                )
            except CalculatorExecutionError as error:
                errors.append(error)

        with patch.object(
            CalculatorExecutor,
            "_signal_process_group",
            side_effect=PermissionError("simulated group signal failure"),
        ):
            worker = threading.Thread(target=invoke)
            worker.start()
            pid_deadline = time.monotonic() + 2.0
            while not descendant_pid_path.exists() and time.monotonic() < pid_deadline:
                time.sleep(0.01)
            assert descendant_pid_path.exists()
            descendant_pid = int(descendant_pid_path.read_text(encoding="utf-8"))
            worker.join(timeout=3.0)
            completed_before_descendant_cleanup = not worker.is_alive()
            with contextlib.suppress(ProcessLookupError):
                os.kill(descendant_pid, execution_module.signal.SIGKILL)
            worker.join(timeout=3.0)

        assert completed_before_descendant_cleanup
        assert not worker.is_alive()
        assert len(errors) == 1
        assert errors[0].record.status is ExecutionStatus.failed_to_terminate
        assert "simulated group signal failure" in (
            errors[0].record.error_message or ""
        )
        on_disk = json.loads(errors[0].record_path.read_text(encoding="utf-8"))
        assert on_disk["status"] == "failed-to-terminate"
        deadline = time.monotonic() + 2.0
        while _process_exists(descendant_pid) and time.monotonic() < deadline:
            time.sleep(0.01)
        assert not _process_exists(descendant_pid)


def test_post_kill_wait_is_bounded_and_reports_termination_failure() -> None:
    process = Mock()
    process.pid = 12345
    process.poll.return_value = None

    with (
        patch.object(
            execution_module,
            "_PROCESS_GROUP_TERMINATION_GRACE_SECONDS",
            0.0,
        ),
        patch.object(execution_module, "_PROCESS_GROUP_KILL_WAIT_SECONDS", 0.02),
        patch.object(execution_module, "_PROCESS_GROUP_POLL_SECONDS", 0.0),
        patch.object(CalculatorExecutor, "_process_group_exists", return_value=True),
        patch.object(CalculatorExecutor, "_signal_process_group") as signal_group,
        pytest.raises(
            execution_module._ProcessTerminationError,
            match="did not terminate after kill",
        ),
    ):
        CalculatorExecutor()._terminate_process_group(process)

    assert signal_group.call_args_list == [
        call(12345, execution_module.signal.SIGTERM),
        call(12345, execution_module.signal.SIGKILL),
    ]
    process.poll.assert_called()
    process.wait.assert_not_called()


def test_timeout_with_capture_failure_records_failed_output() -> None:
    payload = b"output-before-timeout-and-capture-failure"
    real_write_and_flush = CalculatorExecutor()._write_and_flush
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)
        stdout_path = working_directory / "stdout.txt"

        def fail_stdout_capture(
            _executor: CalculatorExecutor,
            destination: BinaryIO,
            chunk: bytes,
        ) -> None:
            if getattr(destination, "name", None) == str(stdout_path):
                raise OSError("simulated retained-output failure")
            real_write_and_flush(destination, chunk)

        with (
            patch.object(
                CalculatorExecutor,
                "_write_and_flush",
                fail_stdout_capture,
            ),
            pytest.raises(CalculatorExecutionError) as caught,
        ):
            CalculatorExecutor().action(
                request=CalculatorExecutionRequest(
                    command=(
                        sys.executable,
                        "-c",
                        (
                            "import sys, time; "
                            f"sys.stdout.buffer.write({payload!r}); "
                            "sys.stdout.buffer.flush(); time.sleep(30)"
                        ),
                    ),
                    working_directory=working_directory,
                    timeout_seconds=0.5,
                    execution_authorized=True,
                )
            )

        assert caught.value.record.status is ExecutionStatus.failed_output
        assert caught.value.record.returncode is None
        assert "timed out" in (caught.value.record.error_message or "")
        assert "stdout capture failed" in (caught.value.record.error_message or "")
        on_disk = json.loads(caught.value.record_path.read_text(encoding="utf-8"))
        assert on_disk["status"] == "failed-output"
        assert on_disk["returncode"] is None


def test_post_timeout_cleanup_error_retains_timeout_detail() -> None:
    real_finish = CalculatorExecutor()._finish_stream_pumps
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)

        def fail_after_finish(
            _executor: CalculatorExecutor,
            pumps: tuple[execution_module._StreamPump, ...],
            *,
            abort_reads: bool = False,
        ) -> None:
            real_finish(pumps, abort_reads=abort_reads)
            raise OSError("simulated retained-output cleanup failure")

        with (
            patch.object(
                CalculatorExecutor,
                "_finish_stream_pumps",
                fail_after_finish,
            ),
            pytest.raises(CalculatorExecutionError) as caught,
        ):
            CalculatorExecutor().action(
                request=CalculatorExecutionRequest(
                    command=(sys.executable, "-c", "import time; time.sleep(30)"),
                    working_directory=working_directory,
                    timeout_seconds=0.25,
                    execution_authorized=True,
                )
            )

        assert caught.value.record.status is ExecutionStatus.failed_output
        assert caught.value.record.returncode is None
        assert "timed out" in (caught.value.record.error_message or "")
        assert "simulated retained-output cleanup failure" in (
            caught.value.record.error_message or ""
        )


def test_records_retained_output_failure_after_draining_process() -> None:
    payload = b"emitted-despite-retention-failure"
    real_write_and_flush = CalculatorExecutor()._write_and_flush
    with tempfile.TemporaryDirectory() as temporary_directory:
        working_directory = Path(temporary_directory)
        stdout_path = working_directory / "stdout.txt"

        def fail_stdout_capture(
            _executor: CalculatorExecutor,
            destination: BinaryIO,
            chunk: bytes,
        ) -> None:
            if getattr(destination, "name", None) == str(stdout_path):
                raise OSError("simulated retained-output failure")
            real_write_and_flush(destination, chunk)

        with (
            patch.object(
                CalculatorExecutor,
                "_write_and_flush",
                fail_stdout_capture,
            ),
            pytest.raises(CalculatorExecutionError) as caught,
        ):
            CalculatorExecutor().action(
                request=CalculatorExecutionRequest(
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
            CalculatorExecutor().action(
                request=CalculatorExecutionRequest(
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


def _process_exists(process_id: int) -> bool:
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        return False
    return True


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
