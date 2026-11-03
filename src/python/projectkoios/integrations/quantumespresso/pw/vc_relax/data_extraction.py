"""Extract native data from variable-cell Quantum ESPRESSO relaxation output."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (
    QePwCapturedStreamDataExtractor,
)
from projectkoios.integrations.quantumespresso.pw.relaxation._stream import (
    extract_streamed_relaxation_sources,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.data import (
    QeRelaxData,
    QeRelaxDataAssembler,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.trajectory import (
    QeRelaxationTrajectoryParser,
)
from projectkoios.integrations.quantumespresso.qexsd.records import QexsdDocument
from projectkoios.simulations.execution import CalculatorExecutionRecord


@dataclass(frozen=True, slots=True)
class QeVcRelaxDataExtractor:
    """Extract variable-cell relaxation data at configured artifact paths."""

    stdout_relative_path: str
    stderr_relative_path: str

    def extract(
        self,
        *,
        stdout_payload: bytes,
        stderr_payload: bytes,
        qexsd_document: QexsdDocument | None = None,
        execution: CalculatorExecutionRecord | None = None,
    ) -> QeRelaxData:
        """Extract native sources and assemble one immutable data object."""
        streams = QePwCapturedStreamDataExtractor(
            stdout_relative_path=self.stdout_relative_path,
            stderr_relative_path=self.stderr_relative_path,
        ).extract(
            stdout_payload=stdout_payload,
            stderr_payload=stderr_payload,
        )
        trajectory = QeRelaxationTrajectoryParser().parse(
            stdout_payload,
            calculation="vc-relax",
            summary=streams.stdout,
        )
        return QeRelaxDataAssembler(
            calculation="vc-relax",
            streams=streams,
            stdout_trajectory=trajectory,
            qexsd_document=qexsd_document,
            execution=execution,
        ).assemble()

    def extract_stream(
        self,
        *,
        stdout_source: BinaryIO,
        stdout_destination: Path,
        stderr_payload: bytes,
        qexsd_document: QexsdDocument | None = None,
        execution: CalculatorExecutionRecord | None = None,
    ) -> QeRelaxData:
        """Persist and parse stdout in one pass without buffering full output."""
        streams, trajectory = extract_streamed_relaxation_sources(
            calculation="vc-relax",
            stdout_source=stdout_source,
            stdout_destination=stdout_destination,
            stderr_payload=stderr_payload,
            stdout_relative_path=self.stdout_relative_path,
            stderr_relative_path=self.stderr_relative_path,
        )
        return QeRelaxDataAssembler(
            calculation="vc-relax",
            streams=streams,
            stdout_trajectory=trajectory,
            qexsd_document=qexsd_document,
            execution=execution,
        ).assemble()
