"""Exact calculator-neutral observations for one process attempt."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from enum import Enum

from projectkoios.physkit.core.actions import DataObjectActionizer
from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.core.results import ResultsObject
from projectkoios.simulations.execution._record_serialization import (
    CalculatorExecutionRecordSerializer,
)
from projectkoios.simulations.execution._records import (
    CalculatorExecutionRecord,
    ExecutionStatus,
)


@dataclass(frozen=True, slots=True)
class CalculatorExecutionContentIdentity(DataObject):
    """Identify exact retained bytes with SHA-256 and byte count.

    Parameters
    ----------
    sha256
        Lowercase hexadecimal SHA-256 digest.
    byte_size
        Nonnegative exact byte count.
    """

    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        if (
            type(self.sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", self.sha256) is None
        ):
            raise ValueError("sha256 must be lowercase hexadecimal")
        if type(self.byte_size) is not int:
            raise TypeError("byte_size must be a built-in int excluding bool")
        if self.byte_size < 0:
            raise ValueError("byte_size must be nonnegative")


@dataclass(frozen=True, slots=True)
class CalculatorExecutionArtifactObservation(DataObject):
    """Retain exact bytes and identity for one execution artifact.

    Parameters
    ----------
    filename
        Portable basename assigned to the artifact.
    content
        Exact immutable artifact bytes.
    content_identity
        SHA-256 and byte count of ``content``.
    """

    filename: str
    content: bytes
    content_identity: CalculatorExecutionContentIdentity

    def __post_init__(self) -> None:
        if (
            type(self.filename) is not str
            or not self.filename
            or self.filename in {".", ".."}
            or "/" in self.filename
            or "\\" in self.filename
        ):
            raise ValueError("filename must be a basename")
        if type(self.content) is not bytes:
            raise TypeError("content must be built-in bytes")
        if type(self.content_identity) is not CalculatorExecutionContentIdentity:
            raise TypeError(
                "content_identity must be CalculatorExecutionContentIdentity"
            )
        observed = CalculatorExecutionContentIdentity(
            sha256=hashlib.sha256(self.content).hexdigest(),
            byte_size=len(self.content),
        )
        if observed != self.content_identity:
            raise ValueError("content does not match content_identity")


class CalculatorExitDisposition(Enum):
    """Classify one normal process exit without exposing numeric conventions."""

    succeeded = "succeeded"
    failed = "failed"


@dataclass(frozen=True, slots=True)
class CalculatorExitCode(DataObject):
    """Retain an exact normal process exit code and expose its disposition.

    Parameters
    ----------
    value
        Exact nonnegative operating-system process exit code. The numeric value is
        retained for provenance and serialization; consumers use ``disposition``.
    """

    value: int

    def __post_init__(self) -> None:
        if type(self.value) is not int:
            raise TypeError("value must be a built-in int excluding bool")
        if self.value < 0:
            raise ValueError("value must be nonnegative")

    @property
    def disposition(self) -> CalculatorExitDisposition:
        """Return the portable success/failure meaning of this normal exit."""
        if self.value == 0:
            return CalculatorExitDisposition.succeeded
        return CalculatorExitDisposition.failed


@dataclass(frozen=True, slots=True)
class CalculatorNormalExit(DataObject):
    """Represent one exact normal process exit."""

    exit_code: CalculatorExitCode

    def __post_init__(self) -> None:
        if type(self.exit_code) is not CalculatorExitCode:
            raise TypeError("exit_code must be CalculatorExitCode")


@dataclass(frozen=True, slots=True)
class CalculatorSignalTermination(DataObject):
    """Represent one exact positive operating-system signal number."""

    signal_number: int

    def __post_init__(self) -> None:
        if type(self.signal_number) is not int:
            raise TypeError("signal_number must be a built-in int excluding bool")
        if self.signal_number <= 0:
            raise ValueError("signal_number must be positive")


@dataclass(frozen=True, slots=True)
class CalculatorTimeout(DataObject):
    """Represent one exact timeout and bounded process-group cleanup result.

    Parameters
    ----------
    timeout_seconds
        Positive finite configured process-attempt timeout in seconds.
    termination_sent
        Whether process-group termination was requested successfully.
    kill_sent
        Whether kill escalation was required after the termination grace interval.
    """

    timeout_seconds: float
    termination_sent: bool
    kill_sent: bool

    def __post_init__(self) -> None:
        if type(self.timeout_seconds) is not float:
            raise TypeError("timeout_seconds must be a built-in float")
        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0.0:
            raise ValueError("timeout_seconds must be positive and finite")
        if type(self.termination_sent) is not bool:
            raise TypeError("termination_sent must be a built-in bool")
        if type(self.kill_sent) is not bool:
            raise TypeError("kill_sent must be a built-in bool")
        if self.kill_sent and not self.termination_sent:
            raise ValueError("kill_sent requires termination_sent")


type CalculatorProcessTermination = (
    CalculatorNormalExit | CalculatorSignalTermination | CalculatorTimeout
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CalculatorExecutionObservationRequest(DataObject):
    """Supply exact terminal facts for calculator-neutral evidence assembly.

    Parameters
    ----------
    record
        Exact provider-owned terminal execution record instance.
    record_filename
        Basename used for the retained execution-record document.
    process_entered
        Whether process creation completed and the external process effect began.
    termination
        Exact normal-exit, signal, or timeout variant when terminal process evidence
        is determinate.
    wall_duration_nanoseconds
        Nonnegative monotonic elapsed duration when the process effect began.
    stdout_bytes, stderr_bytes
        Exact retained stream bytes when each authoritative artifact is available.
    """

    record: CalculatorExecutionRecord
    record_filename: str
    process_entered: bool
    termination: CalculatorProcessTermination | None
    wall_duration_nanoseconds: int | None
    stdout_bytes: bytes | None
    stderr_bytes: bytes | None

    def __post_init__(self) -> None:
        if type(self.record) is not CalculatorExecutionRecord:
            raise TypeError("record must be CalculatorExecutionRecord")
        if (
            type(self.record_filename) is not str
            or not self.record_filename
            or self.record_filename in {".", ".."}
            or "/" in self.record_filename
            or "\\" in self.record_filename
        ):
            raise ValueError("record_filename must be a basename")
        if type(self.process_entered) is not bool:
            raise TypeError("process_entered must be a built-in bool")
        if self.termination is not None and type(self.termination) not in (
            CalculatorNormalExit,
            CalculatorSignalTermination,
            CalculatorTimeout,
        ):
            raise TypeError("termination must be a calculator termination variant")
        if self.wall_duration_nanoseconds is not None:
            if type(self.wall_duration_nanoseconds) is not int:
                raise TypeError(
                    "wall_duration_nanoseconds must be a built-in int or None"
                )
            if self.wall_duration_nanoseconds < 0:
                raise ValueError("wall_duration_nanoseconds must be nonnegative")
        for name, value in (
            ("stdout_bytes", self.stdout_bytes),
            ("stderr_bytes", self.stderr_bytes),
        ):
            if value is not None and type(value) is not bytes:
                raise TypeError(f"{name} must be built-in bytes or None")


@dataclass(frozen=True, slots=True, kw_only=True)
class CalculatorExecutionObservation(ResultsObject):
    """Retain exact mechanical evidence for one calculator process attempt.

    Parameters
    ----------
    record
        Exact provider-owned terminal record instance.
    record_artifact
        Exact canonical ``execution.json`` bytes and content identity.
    process_entered
        Whether the external process effect began.
    termination
        Exact determinate terminal variant, when available.
    wall_duration_nanoseconds
        Monotonic elapsed duration for an entered process.
    stdout, stderr
        Exact retained stream artifact observations when available.

    Notes
    -----
    This record establishes mechanical execution evidence only. It does not establish
    calculator completion, numerical convergence, scientific validity, or acceptance.
    """

    record: CalculatorExecutionRecord
    record_artifact: CalculatorExecutionArtifactObservation
    process_entered: bool
    termination: CalculatorProcessTermination | None
    wall_duration_nanoseconds: int | None
    stdout: CalculatorExecutionArtifactObservation | None
    stderr: CalculatorExecutionArtifactObservation | None

    def __post_init__(self) -> None:
        if type(self.record) is not CalculatorExecutionRecord:
            raise TypeError("record must be CalculatorExecutionRecord")
        if type(self.record_artifact) is not CalculatorExecutionArtifactObservation:
            raise TypeError(
                "record_artifact must be CalculatorExecutionArtifactObservation"
            )
        if type(self.process_entered) is not bool:
            raise TypeError("process_entered must be a built-in bool")
        if self.termination is not None and type(self.termination) not in (
            CalculatorNormalExit,
            CalculatorSignalTermination,
            CalculatorTimeout,
        ):
            raise TypeError("termination must be a calculator termination variant")
        if self.wall_duration_nanoseconds is not None:
            if type(self.wall_duration_nanoseconds) is not int:
                raise TypeError(
                    "wall_duration_nanoseconds must be a built-in int or None"
                )
            if self.wall_duration_nanoseconds < 0:
                raise ValueError("wall_duration_nanoseconds must be nonnegative")
        for name, value in (("stdout", self.stdout), ("stderr", self.stderr)):
            if value is not None and type(value) is not (
                CalculatorExecutionArtifactObservation
            ):
                raise TypeError(
                    f"{name} must be CalculatorExecutionArtifactObservation or None"
                )


@dataclass(frozen=True, slots=True)
class CalculatorExecutionObservationAssembler(
    DataObjectActionizer[
        CalculatorExecutionObservationRequest, CalculatorExecutionObservation
    ]
):
    """Assemble exact mechanical evidence without process or filesystem effects.

    Parameters
    ----------
    serializer
        Exact owner of the retained ``execution.json`` wire bytes.
    """

    serializer: CalculatorExecutionRecordSerializer

    def __post_init__(self) -> None:
        if type(self.serializer) is not CalculatorExecutionRecordSerializer:
            raise TypeError("serializer must be CalculatorExecutionRecordSerializer")

    def action(
        self, *, request: CalculatorExecutionObservationRequest
    ) -> CalculatorExecutionObservation:
        """Return one validated immutable execution observation."""
        if type(request) is not CalculatorExecutionObservationRequest:
            raise TypeError("request must be CalculatorExecutionObservationRequest")
        self._validate_terminal_correlation(request)
        record_bytes = self.serializer.execute(request.record)
        record_artifact = self._artifact(request.record_filename, record_bytes)
        stdout = (
            None
            if request.stdout_bytes is None
            else self._artifact(request.record.stdout_filename, request.stdout_bytes)
        )
        stderr = (
            None
            if request.stderr_bytes is None
            else self._artifact(request.record.stderr_filename, request.stderr_bytes)
        )
        return CalculatorExecutionObservation(
            record=request.record,
            record_artifact=record_artifact,
            process_entered=request.process_entered,
            termination=request.termination,
            wall_duration_nanoseconds=request.wall_duration_nanoseconds,
            stdout=stdout,
            stderr=stderr,
        )

    def _validate_terminal_correlation(
        self, request: CalculatorExecutionObservationRequest
    ) -> None:
        record = request.record
        termination = request.termination
        if request.process_entered:
            if request.wall_duration_nanoseconds is None:
                raise ValueError("entered processes require a monotonic duration")
        elif request.wall_duration_nanoseconds is not None or termination is not None:
            raise ValueError(
                "pre-entry observations cannot carry duration or termination evidence"
            )
        if (
            record.status
            in (
                ExecutionStatus.failed_preflight,
                ExecutionStatus.failed_to_start,
            )
            and request.process_entered
        ):
            raise ValueError("pre-entry execution status cannot mark process entry")
        if (
            record.status
            in (
                ExecutionStatus.succeeded,
                ExecutionStatus.failed,
                ExecutionStatus.timed_out,
                ExecutionStatus.failed_to_terminate,
            )
            and not request.process_entered
        ):
            raise ValueError("post-entry execution status requires process entry")
        if record.status is ExecutionStatus.succeeded:
            if type(termination) is not CalculatorNormalExit:
                raise ValueError("successful execution requires a normal exit")
            if (
                termination.exit_code.disposition
                is not CalculatorExitDisposition.succeeded
                or record.returncode != termination.exit_code.value
            ):
                raise ValueError("successful execution requires a successful exit")
        elif record.status is ExecutionStatus.failed:
            if type(termination) is CalculatorNormalExit:
                if (
                    termination.exit_code.disposition
                    is not CalculatorExitDisposition.failed
                    or record.returncode != termination.exit_code.value
                ):
                    raise ValueError(
                        "failed normal exit requires one matching failed exit code"
                    )
            elif type(termination) is CalculatorSignalTermination:
                if record.returncode != -termination.signal_number:
                    raise ValueError(
                        "signal termination must match the negative record return code"
                    )
            else:
                raise ValueError(
                    "failed execution requires normal-exit or signal evidence"
                )
        elif record.status is ExecutionStatus.timed_out:
            if (
                type(termination) is not CalculatorTimeout
                or record.returncode is not None
            ):
                raise ValueError(
                    "timed-out execution requires timeout evidence and no return code"
                )
        elif record.status is ExecutionStatus.failed_to_terminate:
            if termination is not None:
                raise ValueError(
                    "failed-to-terminate execution cannot claim terminal "
                    "process evidence"
                )
        elif (
            record.status
            in (
                ExecutionStatus.failed_preflight,
                ExecutionStatus.failed_to_start,
            )
            and termination is not None
        ):
            raise ValueError("pre-entry execution status cannot carry termination")

    def _artifact(
        self, filename: str, content: bytes
    ) -> CalculatorExecutionArtifactObservation:
        identity = CalculatorExecutionContentIdentity(
            sha256=hashlib.sha256(content).hexdigest(), byte_size=len(content)
        )
        return CalculatorExecutionArtifactObservation(
            filename=filename,
            content=content,
            content_identity=identity,
        )
