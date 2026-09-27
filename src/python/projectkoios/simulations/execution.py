"""Execute explicit calculator commands with durable failure records."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Never


class ExecutionStatus(StrEnum):
    """Classify the terminal status of one calculator process attempt."""

    succeeded = "succeeded"
    failed = "failed"
    failed_preflight = "failed-preflight"
    failed_to_start = "failed-to-start"
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
            if self.timeout_seconds <= 0.0:
                raise ValueError("timeout_seconds must be positive")


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
    """Report a recorded calculator start, timeout, or exit failure."""

    record: CalculatorExecutionRecord
    record_path: Path

    def __init__(self, record: CalculatorExecutionRecord, record_path: Path) -> None:
        self.record = record
        self.record_path = record_path
        super().__init__(
            f"calculator execution {record.status.value}; record: {record_path}"
        )


@dataclass(frozen=True, slots=True)
class CalculatorExecutor:
    """Run one no-shell command and persist its terminal record before returning."""

    def execute(self, request: CalculatorExecutionRequest) -> CalculatorExecutionRecord:
        """Execute, record terminal state, and raise after recording any failure."""
        if type(request) is not CalculatorExecutionRequest:
            raise TypeError("request must be a CalculatorExecutionRequest")
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

        try:
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                completed = subprocess.run(
                    request.command,
                    cwd=request.working_directory,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=stderr,
                    timeout=request.timeout_seconds,
                    check=False,
                    shell=False,
                )
        except subprocess.TimeoutExpired as error:
            record = _error_record(
                request,
                ExecutionStatus.timed_out,
                type(error).__name__,
                str(error),
            )
            _write_record(record_path, record)
            raise CalculatorExecutionError(record, record_path) from error
        except OSError as error:
            record = _error_record(
                request,
                ExecutionStatus.failed_to_start,
                type(error).__name__,
                str(error),
            )
            _write_record(record_path, record)
            raise CalculatorExecutionError(record, record_path) from error

        status = (
            ExecutionStatus.succeeded
            if completed.returncode == 0
            else ExecutionStatus.failed
        )
        record = CalculatorExecutionRecord(
            command=request.command,
            working_directory=str(request.working_directory.resolve()),
            status=status,
            returncode=completed.returncode,
            stdout_filename=request.stdout_filename,
            stderr_filename=request.stderr_filename,
            required_input_filenames=request.required_input_filenames,
        )
        _write_record(record_path, record)
        if status is not ExecutionStatus.succeeded:
            raise CalculatorExecutionError(record, record_path)
        return record

    def record_preflight_failure(
        self,
        request: CalculatorExecutionRequest,
        error: Exception,
    ) -> Never:
        """Write a failed-preflight record and then raise its execution error."""
        if type(request) is not CalculatorExecutionRequest:
            raise TypeError("request must be a CalculatorExecutionRequest")
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


def _error_record(
    request: CalculatorExecutionRequest,
    status: ExecutionStatus,
    error_type: str,
    error_message: str,
) -> CalculatorExecutionRecord:
    return CalculatorExecutionRecord(
        command=request.command,
        working_directory=str(request.working_directory.resolve()),
        status=status,
        returncode=None,
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
