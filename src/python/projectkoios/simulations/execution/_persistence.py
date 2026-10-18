"""Canonical terminal-record construction and atomic persistence."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from projectkoios.simulations.execution._records import (
    CalculatorExecutionRecord,
    CalculatorExecutionRequest,
    ExecutionStatus,
)


class _ExecutionRecordSupport:
    """Provide terminal-record construction and persistence to the executor."""

    __slots__ = ()

    def _error_record(
        self,
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

    def _write_record(
        self,
        path: Path,
        record: CalculatorExecutionRecord,
    ) -> None:
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
