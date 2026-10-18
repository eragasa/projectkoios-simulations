"""Authorized calculator process execution and terminal classification."""

from __future__ import annotations

import os
import subprocess
from typing import BinaryIO, Never, cast

from projectkoios.physkit.core.actions import DataObjectActionizer
from projectkoios.simulations.execution._persistence import _ExecutionRecordSupport
from projectkoios.simulations.execution._process_group import (
    _ProcessGroupSupport,
    _ProcessTerminationError,
)
from projectkoios.simulations.execution._records import (
    CalculatorExecutionError,
    CalculatorExecutionRecord,
    CalculatorExecutionRequest,
    CalculatorOutputEmissionError,
    ExecutionStatus,
)
from projectkoios.simulations.execution._streaming import (
    _StreamPump,
    _StreamPumpFailure,
    _StreamSupport,
)


class CalculatorExecutor(
    _StreamSupport,
    _ProcessGroupSupport,
    _ExecutionRecordSupport,
    DataObjectActionizer[CalculatorExecutionRequest, CalculatorExecutionRecord],
):
    """Run one no-shell command and persist its terminal record before returning."""

    __slots__ = ()

    def action(
        self,
        *,
        request: CalculatorExecutionRequest,
    ) -> CalculatorExecutionRecord:
        """Execute one process, tee native streams, and record terminal state."""
        if type(request) is not CalculatorExecutionRequest:
            raise TypeError("request must be a CalculatorExecutionRequest")
        if not request.execution_authorized:
            raise PermissionError("calculator execution is not authorized")
        stdout_path = request.working_directory / request.stdout_filename
        stderr_path = request.working_directory / request.stderr_filename
        record_path = request.working_directory / request.record_filename
        for path in (stdout_path, stderr_path, record_path):
            if path.is_symlink():
                raise ValueError("execution outputs must not be symbolic links")
        for filename in request.required_input_filenames:
            path = request.working_directory / filename
            if not path.is_file() or path.is_symlink():
                error = FileNotFoundError(
                    f"required calculator input file not found: {filename}"
                )
                self.record_preflight_failure(request=request, error=error)
        if os.name != "posix":
            self.record_preflight_failure(
                request=request,
                error=RuntimeError(
                    "calculator execution requires POSIX process-group isolation"
                ),
            )

        timeout_error: subprocess.TimeoutExpired | None = None
        termination_error: _ProcessTerminationError | None = None
        stream_failures: list[_StreamPumpFailure] = []
        returncode: int | None = None
        process: subprocess.Popen[bytes] | None = None
        try:
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                try:
                    process = subprocess.Popen(
                        request.command,
                        cwd=request.working_directory,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=False,
                        bufsize=0,
                        start_new_session=True,
                    )
                except OSError as error:
                    record = self._error_record(
                        request,
                        ExecutionStatus.failed_to_start,
                        type(error).__name__,
                        str(error),
                    )
                    self._write_record(record_path, record)
                    raise CalculatorExecutionError(record, record_path) from error
                assert process.stdout is not None
                assert process.stderr is not None
                pumps: list[_StreamPump] = []
                try:
                    pumps.append(
                        self._start_stream_pump(
                            name="stdout",
                            source=cast(BinaryIO, process.stdout),
                            destination=stdout,
                            failures=stream_failures,
                        )
                    )
                    pumps.append(
                        self._start_stream_pump(
                            name="stderr",
                            source=cast(BinaryIO, process.stderr),
                            destination=stderr,
                            failures=stream_failures,
                        )
                    )
                    try:
                        returncode = process.wait(timeout=request.timeout_seconds)
                    except subprocess.TimeoutExpired as error:
                        timeout_error = error
                        try:
                            returncode = self._terminate_process_group(
                                process
                            ).returncode
                        except _ProcessTerminationError as termination:
                            termination_error = termination
                finally:
                    if process.poll() is None and termination_error is None:
                        try:
                            self._terminate_process_group(process)
                        except _ProcessTerminationError as termination:
                            termination_error = termination
                    self._finish_stream_pumps(
                        tuple(pumps),
                        abort_reads=termination_error is not None,
                    )
        except CalculatorExecutionError:
            raise
        except Exception as error:
            message = str(error)
            if timeout_error is not None:
                message = f"{timeout_error}; {message}"
            if termination_error is not None:
                message = f"{termination_error}; {message}"
            record = self._error_record(
                request,
                ExecutionStatus.failed_output,
                type(error).__name__,
                message,
                returncode=(
                    None
                    if timeout_error is not None or process is None
                    else process.returncode
                ),
            )
            self._write_record(record_path, record)
            raise CalculatorExecutionError(record, record_path) from error

        assert process is not None
        capture_failures = [
            failure for failure in stream_failures if failure.stage != "emission"
        ]
        if capture_failures:
            failure = capture_failures[0]
            message = self._stream_failure_message(stream_failures)
            if timeout_error is not None:
                message = f"{timeout_error}; {message}"
            if termination_error is not None:
                message = f"{termination_error}; {message}"
            record = self._error_record(
                request,
                ExecutionStatus.failed_output,
                type(failure.error).__name__,
                message,
                returncode=None if timeout_error is not None else returncode,
            )
            self._write_record(record_path, record)
            raise CalculatorExecutionError(record, record_path) from failure.error

        if termination_error is not None:
            message = str(termination_error)
            if timeout_error is not None:
                message = f"{timeout_error}; {message}"
            record = self._error_record(
                request,
                ExecutionStatus.failed_to_terminate,
                type(termination_error).__name__,
                self._combine_error_message(message, stream_failures),
                returncode=process.returncode,
            )
            self._write_record(record_path, record)
            raise CalculatorExecutionError(record, record_path) from termination_error

        if timeout_error is not None:
            record = self._error_record(
                request,
                ExecutionStatus.timed_out,
                type(timeout_error).__name__,
                self._combine_error_message(str(timeout_error), stream_failures),
            )
            self._write_record(record_path, record)
            raise CalculatorExecutionError(record, record_path) from timeout_error

        assert returncode is not None
        status = (
            ExecutionStatus.succeeded if returncode == 0 else ExecutionStatus.failed
        )
        record = CalculatorExecutionRecord(
            command=request.command,
            working_directory=str(request.working_directory.resolve()),
            status=status,
            returncode=returncode,
            stdout_filename=request.stdout_filename,
            stderr_filename=request.stderr_filename,
            required_input_filenames=request.required_input_filenames,
        )
        self._write_record(record_path, record)
        if status is not ExecutionStatus.succeeded:
            raise CalculatorExecutionError(record, record_path)
        if stream_failures:
            failure = stream_failures[0]
            raise CalculatorOutputEmissionError(
                record,
                record_path,
                self._stream_failure_message(stream_failures),
            ) from failure.error
        return record

    def record_preflight_failure(
        self,
        *,
        request: CalculatorExecutionRequest,
        error: Exception,
    ) -> Never:
        """Write a failed-preflight record and then raise its execution error."""
        if type(request) is not CalculatorExecutionRequest:
            raise TypeError("request must be a CalculatorExecutionRequest")
        if not request.execution_authorized:
            raise PermissionError("calculator execution is not authorized")
        if not isinstance(error, Exception):
            raise TypeError("error must be an Exception")
        record_path = request.working_directory / request.record_filename
        record = self._error_record(
            request,
            ExecutionStatus.failed_preflight,
            type(error).__name__,
            str(error),
        )
        self._write_record(record_path, record)
        raise CalculatorExecutionError(record, record_path) from error
