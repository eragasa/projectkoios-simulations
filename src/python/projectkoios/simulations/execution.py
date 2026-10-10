"""Execute explicit calculator commands with durable failure records."""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import BinaryIO, Never, cast

_STREAM_CHUNK_SIZE = 64 * 1024
_STREAM_JOIN_TIMEOUT_SECONDS = 5.0


class ExecutionStatus(StrEnum):
    """Classify the terminal status of one calculator process attempt."""

    succeeded = "succeeded"
    failed = "failed"
    failed_preflight = "failed-preflight"
    failed_to_start = "failed-to-start"
    failed_output = "failed-output"
    timed_out = "timed-out"


@dataclass(frozen=True, slots=True)
class CalculatorExecutionRequest:
    """Declare one explicit no-shell calculator process invocation."""

    command: tuple[str, ...]
    working_directory: Path
    stdout_filename: str = "stdout.txt"
    stderr_filename: str = "stderr.txt"
    record_filename: str = "execution.json"
    required_input_filenames: tuple[str, ...] = ()
    timeout_seconds: float | None = None
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        if type(self.command) is not tuple or not self.command:
            raise ValueError("command must be a nonempty tuple")
        if any(
            type(argument) is not str or not argument or "\0" in argument
            for argument in self.command
        ):
            raise ValueError("command must contain nonempty strings without null bytes")
        if not isinstance(self.working_directory, Path):
            raise TypeError("working_directory must be a Path")
        if not self.working_directory.is_dir() or self.working_directory.is_symlink():
            raise ValueError(
                "working_directory must be an existing nonsymlink directory"
            )
        for label, filename in (
            ("stdout_filename", self.stdout_filename),
            ("stderr_filename", self.stderr_filename),
            ("record_filename", self.record_filename),
        ):
            if (
                type(filename) is not str
                or not filename
                or filename in {".", ".."}
                or "/" in filename
                or "\\" in filename
            ):
                raise ValueError(f"{label} must be a basename")
        if len({self.stdout_filename, self.stderr_filename, self.record_filename}) != 3:
            raise ValueError("execution output filenames must be distinct")
        if type(self.required_input_filenames) is not tuple:
            raise TypeError("required_input_filenames must be a tuple")
        if len(set(self.required_input_filenames)) != len(
            self.required_input_filenames
        ):
            raise ValueError("required_input_filenames must be unique")
        for filename in self.required_input_filenames:
            if (
                type(filename) is not str
                or not filename
                or filename in {".", ".."}
                or "/" in filename
                or "\\" in filename
            ):
                raise ValueError("required input filenames must be basenames")
        if self.timeout_seconds is not None:
            if type(self.timeout_seconds) is not float:
                raise TypeError("timeout_seconds must be a float or None")
            if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0.0:
                raise ValueError("timeout_seconds must be positive and finite")
        if type(self.execution_authorized) is not bool:
            raise TypeError("execution_authorized must be a bool")


@dataclass(frozen=True, slots=True)
class CalculatorExecutionRecord:
    """Describe one terminal calculator process attempt."""

    command: tuple[str, ...]
    working_directory: str
    status: ExecutionStatus
    returncode: int | None
    stdout_filename: str
    stderr_filename: str
    required_input_filenames: tuple[str, ...]
    error_type: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if type(self.command) is not tuple or not self.command:
            raise ValueError("record command must be a nonempty tuple")
        if type(self.working_directory) is not str or not self.working_directory:
            raise ValueError("record working_directory must be nonempty")
        if type(self.status) is not ExecutionStatus:
            raise TypeError("record status must be an ExecutionStatus")
        if self.returncode is not None and type(self.returncode) is not int:
            raise TypeError("record returncode must be an integer or None")
        if type(self.required_input_filenames) is not tuple:
            raise TypeError("record required_input_filenames must be a tuple")
        if self.status is ExecutionStatus.succeeded and self.returncode != 0:
            raise ValueError("successful execution record must have returncode zero")
        if self.status is ExecutionStatus.failed and (
            self.returncode is None or self.returncode == 0
        ):
            raise ValueError("failed execution record must have nonzero returncode")
        if (self.error_type is None) is not (self.error_message is None):
            raise ValueError("error_type and error_message must both be set or omitted")


class CalculatorExecutionError(RuntimeError):
    """Report a recorded preflight, process, or retained-output failure."""

    record: CalculatorExecutionRecord
    record_path: Path

    def __init__(self, record: CalculatorExecutionRecord, record_path: Path) -> None:
        self.record = record
        self.record_path = record_path
        super().__init__(
            f"calculator execution {record.status.value}; record: {record_path}"
        )


class CalculatorOutputEmissionError(RuntimeError):
    """Report failed live emission after retaining the calculator output."""

    record: CalculatorExecutionRecord
    record_path: Path

    def __init__(
        self,
        record: CalculatorExecutionRecord,
        record_path: Path,
        message: str,
    ) -> None:
        self.record = record
        self.record_path = record_path
        super().__init__(
            f"calculator output emission failed: {message}; record: {record_path}"
        )


@dataclass(frozen=True, slots=True)
class CalculatorExecutor:
    """Run one no-shell command and persist its terminal record before returning."""

    def execute(self, request: CalculatorExecutionRequest) -> CalculatorExecutionRecord:
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
                self.record_preflight_failure(request, error)

        timeout_error: subprocess.TimeoutExpired | None = None
        stream_failures: list[_StreamPumpFailure] = []
        returncode: int | None = None
        try:
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                process = subprocess.Popen(
                    request.command,
                    cwd=request.working_directory,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                    bufsize=0,
                )
                assert process.stdout is not None
                assert process.stderr is not None
                pumps = (
                    _start_stream_pump(
                        name="stdout",
                        source=cast(BinaryIO, process.stdout),
                        destination=stdout,
                        emit=_emit_output,
                        failures=stream_failures,
                    ),
                    _start_stream_pump(
                        name="stderr",
                        source=cast(BinaryIO, process.stderr),
                        destination=stderr,
                        emit=_emit_output,
                        failures=stream_failures,
                    ),
                )
                try:
                    returncode = process.wait(timeout=request.timeout_seconds)
                except subprocess.TimeoutExpired as error:
                    timeout_error = error
                    process.kill()
                    returncode = process.wait()
                finally:
                    _finish_stream_pumps(pumps)
        except OSError as error:
            record = _error_record(
                request,
                ExecutionStatus.failed_to_start,
                type(error).__name__,
                str(error),
            )
            _write_record(record_path, record)
            raise CalculatorExecutionError(record, record_path) from error

        if timeout_error is not None:
            record = _error_record(
                request,
                ExecutionStatus.timed_out,
                type(timeout_error).__name__,
                _combine_error_message(str(timeout_error), stream_failures),
            )
            _write_record(record_path, record)
            raise CalculatorExecutionError(record, record_path) from timeout_error

        capture_failures = [
            failure for failure in stream_failures if failure.stage != "emission"
        ]
        if capture_failures:
            failure = capture_failures[0]
            record = _error_record(
                request,
                ExecutionStatus.failed_output,
                type(failure.error).__name__,
                _stream_failure_message(stream_failures),
                returncode=returncode,
            )
            _write_record(record_path, record)
            raise CalculatorExecutionError(record, record_path) from failure.error

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
        _write_record(record_path, record)
        if status is not ExecutionStatus.succeeded:
            raise CalculatorExecutionError(record, record_path)
        if stream_failures:
            failure = stream_failures[0]
            raise CalculatorOutputEmissionError(
                record,
                record_path,
                _stream_failure_message(stream_failures),
            ) from failure.error
        return record

    def record_preflight_failure(
        self,
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
        record = _error_record(
            request,
            ExecutionStatus.failed_preflight,
            type(error).__name__,
            str(error),
        )
        _write_record(record_path, record)
        raise CalculatorExecutionError(record, record_path) from error


@dataclass(frozen=True, slots=True)
class _StreamPumpFailure:
    """Retain one stream capture or live-emission failure for terminal recording."""

    stream_name: str
    stage: str
    error: Exception


@dataclass(frozen=True, slots=True)
class _StreamPump:
    """Retain one source pipe and its active bounded drain thread."""

    stream_name: str
    source: BinaryIO
    thread: threading.Thread
    failures: list[_StreamPumpFailure]


def _start_stream_pump(
    *,
    name: str,
    source: BinaryIO,
    destination: BinaryIO,
    emit: Callable[[str, bytes], None],
    failures: list[_StreamPumpFailure],
) -> _StreamPump:
    thread = threading.Thread(
        name=f"calculator-{name}-pump",
        target=_pump_stream,
        kwargs={
            "name": name,
            "source": source,
            "destination": destination,
            "emit": emit,
            "failures": failures,
        },
        daemon=True,
    )
    thread.start()
    return _StreamPump(
        stream_name=name,
        source=source,
        thread=thread,
        failures=failures,
    )


def _pump_stream(
    *,
    name: str,
    source: BinaryIO,
    destination: BinaryIO,
    emit: Callable[[str, bytes], None],
    failures: list[_StreamPumpFailure],
) -> None:
    capture_enabled = True
    emission_enabled = True
    while True:
        try:
            chunk = source.read(_STREAM_CHUNK_SIZE)
        except Exception as error:
            failures.append(_StreamPumpFailure(name, "read", error))
            return
        if not chunk:
            return
        if capture_enabled:
            try:
                _write_and_flush(destination, chunk)
            except Exception as error:
                failures.append(_StreamPumpFailure(name, "capture", error))
                capture_enabled = False
        if emission_enabled:
            try:
                emit(name, chunk)
            except Exception as error:
                failures.append(_StreamPumpFailure(name, "emission", error))
                emission_enabled = False


def _finish_stream_pumps(pumps: tuple[_StreamPump, ...]) -> None:
    for pump in pumps:
        pump.thread.join(timeout=_STREAM_JOIN_TIMEOUT_SECONDS)
    for pump in pumps:
        if pump.thread.is_alive():
            pump.source.close()
            pump.thread.join(timeout=_STREAM_JOIN_TIMEOUT_SECONDS)
        else:
            pump.source.close()
        if pump.thread.is_alive():
            pump.failures.append(
                _StreamPumpFailure(
                    pump.stream_name,
                    "join",
                    TimeoutError("stream pump did not terminate"),
                )
            )


def _emit_output(stream_name: str, chunk: bytes) -> None:
    stream: object
    if stream_name == "stdout":
        stream = sys.stdout
    elif stream_name == "stderr":
        stream = sys.stderr
    else:
        raise ValueError(f"unsupported output stream: {stream_name}")
    candidate = getattr(stream, "buffer", None)
    if candidate is None:
        raise RuntimeError(f"parent {stream_name} does not expose a binary buffer")
    _write_and_flush(cast(BinaryIO, candidate), chunk)


def _write_and_flush(destination: BinaryIO, chunk: bytes) -> None:
    offset = 0
    while offset < len(chunk):
        written = destination.write(chunk[offset:])
        if written is None or written <= 0:
            raise OSError("output stream did not accept bytes")
        offset += written
    destination.flush()


def _stream_failure_message(failures: list[_StreamPumpFailure]) -> str:
    return "; ".join(
        f"{failure.stream_name} {failure.stage} failed: {failure.error}"
        for failure in failures
    )


def _combine_error_message(
    primary: str,
    failures: list[_StreamPumpFailure],
) -> str:
    if not failures:
        return primary
    return f"{primary}; {_stream_failure_message(failures)}"


def _error_record(
    request: CalculatorExecutionRequest,
    status: ExecutionStatus,
    error_type: str,
    error_message: str,
    *,
    returncode: int | None = None,
) -> CalculatorExecutionRecord:
    return CalculatorExecutionRecord(
        command=request.command,
        working_directory=str(request.working_directory.resolve()),
        status=status,
        returncode=returncode,
        stdout_filename=request.stdout_filename,
        stderr_filename=request.stderr_filename,
        required_input_filenames=request.required_input_filenames,
        error_type=error_type,
        error_message=error_message,
    )


def _write_record(path: Path, record: CalculatorExecutionRecord) -> None:
    payload = (
        json.dumps(
            {
                "command": record.command,
                "error_message": record.error_message,
                "error_type": record.error_type,
                "required_input_filenames": record.required_input_filenames,
                "returncode": record.returncode,
                "schema_version": 1,
                "status": record.status.value,
                "stderr_filename": record.stderr_filename,
                "stdout_filename": record.stdout_filename,
                "working_directory": record.working_directory,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
    finally:
        if temporary_name is not None and os.path.exists(temporary_name):
            os.unlink(temporary_name)
