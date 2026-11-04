from __future__ import annotations

import dataclasses
import hashlib
import json

import pytest

from projectkoios.simulations.execution import (
    CalculatorExecutionObservation,
    CalculatorExecutionObservationAssembler,
    CalculatorExecutionObservationRequest,
    CalculatorExecutionRecord,
    CalculatorExecutionRecordSerializer,
    CalculatorExitCode,
    CalculatorExitDisposition,
    CalculatorNormalExit,
    CalculatorSignalTermination,
    CalculatorTimeout,
    ExecutionStatus,
)

pytestmark = pytest.mark.software_verification


class TestCalculatorExecutionObservationAssembler:
    def test_exit_code_exposes_disposition_without_consumer_magic_numbers(self) -> None:
        successful_exit = CalculatorExitCode(0)
        failed_exit = CalculatorExitCode(7)

        assert successful_exit.disposition is CalculatorExitDisposition.succeeded
        assert failed_exit.disposition is CalculatorExitDisposition.failed
        with pytest.raises(TypeError, match="built-in int"):
            CalculatorExitCode(True)
        with pytest.raises(ValueError, match="nonnegative"):
            CalculatorExitCode(-1)

    def test_assembles_exact_success_evidence_without_effects(self) -> None:
        record = self._record(
            status=ExecutionStatus.succeeded,
            returncode=0,
        )
        stdout_bytes = b"complete\n"
        stderr_bytes = b""
        successful_exit = CalculatorExitCode(0)
        assembler = CalculatorExecutionObservationAssembler(
            CalculatorExecutionRecordSerializer(schema_version=1)
        )

        result = assembler.action(
            request=CalculatorExecutionObservationRequest(
                record=record,
                record_filename="execution.json",
                process_entered=True,
                termination=CalculatorNormalExit(successful_exit),
                wall_duration_nanoseconds=17,
                stdout_bytes=stdout_bytes,
                stderr_bytes=stderr_bytes,
            )
        )

        assert type(result) is CalculatorExecutionObservation
        assert result.record is record
        assert result.process_entered is True
        assert result.termination == CalculatorNormalExit(successful_exit)
        assert successful_exit.disposition is CalculatorExitDisposition.succeeded
        assert result.wall_duration_nanoseconds == 17
        assert result.stdout is not None
        assert result.stderr is not None
        assert result.stdout.content is stdout_bytes
        assert result.stderr.content is stderr_bytes
        assert (
            result.stdout.content_identity.sha256
            == hashlib.sha256(stdout_bytes).hexdigest()
        )
        assert result.stdout.content_identity.byte_size == len(stdout_bytes)
        assert result.record_artifact.filename == "execution.json"
        assert json.loads(result.record_artifact.content) == {
            "command": ["pw.x", "-in", "pw.in"],
            "error_message": None,
            "error_type": None,
            "required_input_filenames": ["pw.in", "Si.upf"],
            "returncode": 0,
            "schema_version": 1,
            "status": "succeeded",
            "stderr_filename": "stderr.txt",
            "stdout_filename": "stdout.txt",
            "working_directory": "/attempt",
        }
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.process_entered = False  # type: ignore[misc]

    def test_accepts_exact_signal_and_timeout_variants(self) -> None:
        assembler = CalculatorExecutionObservationAssembler(
            CalculatorExecutionRecordSerializer(schema_version=1)
        )
        signal_record = self._record(
            status=ExecutionStatus.failed,
            returncode=-15,
        )
        timeout_record = self._record(
            status=ExecutionStatus.timed_out,
            returncode=None,
            error_type="TimeoutExpired",
            error_message="bounded fixture timeout",
        )

        signal_result = assembler.action(
            request=CalculatorExecutionObservationRequest(
                record=signal_record,
                record_filename="execution.json",
                process_entered=True,
                termination=CalculatorSignalTermination(15),
                wall_duration_nanoseconds=23,
                stdout_bytes=b"partial",
                stderr_bytes=b"",
            )
        )
        timeout_result = assembler.action(
            request=CalculatorExecutionObservationRequest(
                record=timeout_record,
                record_filename="execution.json",
                process_entered=True,
                termination=CalculatorTimeout(
                    timeout_seconds=0.5,
                    termination_sent=True,
                    kill_sent=False,
                ),
                wall_duration_nanoseconds=500_000_000,
                stdout_bytes=b"partial",
                stderr_bytes=b"",
            )
        )

        assert signal_result.termination == CalculatorSignalTermination(15)
        assert timeout_result.termination == CalculatorTimeout(
            timeout_seconds=0.5,
            termination_sent=True,
            kill_sent=False,
        )

    def test_rejects_return_code_inference_that_disagrees_with_exact_variant(
        self,
    ) -> None:
        assembler = CalculatorExecutionObservationAssembler(
            CalculatorExecutionRecordSerializer(schema_version=1)
        )
        record = self._record(status=ExecutionStatus.failed, returncode=7)

        with pytest.raises(ValueError, match="negative record return code"):
            assembler.action(
                request=CalculatorExecutionObservationRequest(
                    record=record,
                    record_filename="execution.json",
                    process_entered=True,
                    termination=CalculatorSignalTermination(15),
                    wall_duration_nanoseconds=29,
                    stdout_bytes=b"",
                    stderr_bytes=b"failed",
                )
            )

    def test_rejects_termination_evidence_for_pre_entry_failure(self) -> None:
        assembler = CalculatorExecutionObservationAssembler(
            CalculatorExecutionRecordSerializer(schema_version=1)
        )
        record = self._record(
            status=ExecutionStatus.failed_to_start,
            returncode=None,
            error_type="FileNotFoundError",
            error_message="fixture executable missing",
        )

        with pytest.raises(ValueError, match="pre-entry observations"):
            assembler.action(
                request=CalculatorExecutionObservationRequest(
                    record=record,
                    record_filename="execution.json",
                    process_entered=False,
                    termination=CalculatorNormalExit(CalculatorExitCode(0)),
                    wall_duration_nanoseconds=None,
                    stdout_bytes=b"",
                    stderr_bytes=b"",
                )
            )

    def test_public_serializer_preserves_the_established_wire(self) -> None:
        record = self._record(
            status=ExecutionStatus.failed_preflight,
            returncode=None,
            error_type="FileNotFoundError",
            error_message="missing required input",
        )
        serializer = CalculatorExecutionRecordSerializer(schema_version=1)

        payload = serializer.execute(record)

        assert payload.endswith(b"\n")
        assert json.loads(payload) == {
            "command": ["pw.x", "-in", "pw.in"],
            "error_message": "missing required input",
            "error_type": "FileNotFoundError",
            "required_input_filenames": ["pw.in", "Si.upf"],
            "returncode": None,
            "schema_version": 1,
            "status": "failed-preflight",
            "stderr_filename": "stderr.txt",
            "stdout_filename": "stdout.txt",
            "working_directory": "/attempt",
        }

    def _record(
        self,
        *,
        status: ExecutionStatus,
        returncode: int | None,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> CalculatorExecutionRecord:
        return CalculatorExecutionRecord(
            command=("pw.x", "-in", "pw.in"),
            working_directory="/attempt",
            status=status,
            returncode=returncode,
            stdout_filename="stdout.txt",
            stderr_filename="stderr.txt",
            required_input_filenames=("pw.in", "Si.upf"),
            error_type=error_type,
            error_message=error_message,
        )
