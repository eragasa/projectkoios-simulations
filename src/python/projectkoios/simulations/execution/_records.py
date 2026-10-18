"""Immutable records and terminal errors for calculator execution."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.core.results import ResultsObject


class ExecutionStatus(StrEnum):
    """Classify the terminal status of one calculator process attempt."""

    succeeded = "succeeded"
    failed = "failed"
    failed_preflight = "failed-preflight"
    failed_to_start = "failed-to-start"
    failed_to_terminate = "failed-to-terminate"
    failed_output = "failed-output"
    timed_out = "timed-out"


@dataclass(frozen=True, slots=True)
class CalculatorExecutionRequest(DataObject):
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
class CalculatorExecutionRecord(ResultsObject):
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
