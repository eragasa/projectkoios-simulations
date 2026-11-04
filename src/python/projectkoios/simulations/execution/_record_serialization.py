"""Canonical public serialization for calculator execution records."""

from __future__ import annotations

import json
from dataclasses import dataclass

from projectkoios.simulations.execution._records import CalculatorExecutionRecord


@dataclass(frozen=True, slots=True)
class CalculatorExecutionRecordSerializer:
    """Serialize the established ``execution.json`` wire without filesystem effects.

    Parameters
    ----------
    schema_version
        Exact supported execution-record schema version. Only version one is defined.
    """

    schema_version: int

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int:
            raise TypeError("schema_version must be a built-in int excluding bool")
        if self.schema_version != 1:
            raise ValueError("only execution-record schema version one is supported")

    def execute(self, record: CalculatorExecutionRecord) -> bytes:
        """Return deterministic UTF-8 ``execution.json`` bytes."""
        if type(record) is not CalculatorExecutionRecord:
            raise TypeError("record must be CalculatorExecutionRecord")
        payload = {
            "command": record.command,
            "error_message": record.error_message,
            "error_type": record.error_type,
            "required_input_filenames": record.required_input_filenames,
            "returncode": record.returncode,
            "schema_version": self.schema_version,
            "status": record.status.value,
            "stderr_filename": record.stderr_filename,
            "stdout_filename": record.stdout_filename,
            "working_directory": record.working_directory,
        }
        return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
