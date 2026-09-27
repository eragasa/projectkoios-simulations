"""Extract native data from variable-cell Quantum ESPRESSO relaxation output."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (  # noqa: E501
    QePwCapturedStreamData,
    QePwCapturedStreamDataExtractor,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.structure import (  # noqa: E501
    QeQexsdFinalStructure,
    QeQexsdFinalStructureExtractor,
)


@dataclass(frozen=True, slots=True)
class QeVcRelaxData:
    """Retain variable-cell relaxation streams and optional final structure."""

    streams: QePwCapturedStreamData
    final_structure: QeQexsdFinalStructure | None = None

    def __post_init__(self) -> None:
        if type(self.streams) is not QePwCapturedStreamData:
            raise TypeError("streams must be QePwCapturedStreamData")
        if self.final_structure is not None and (
            type(self.final_structure) is not QeQexsdFinalStructure
        ):
            raise TypeError("final_structure must be QeQexsdFinalStructure or None")


@dataclass(frozen=True, slots=True)
class QeVcRelaxDataExtractor:
    """Own variable-cell extraction while reusing ``pw.x`` primitives."""

    def extract(
        self,
        *,
        stdout_payload: bytes,
        stderr_payload: bytes,
        qexsd_document: object | None = None,
        stdout_relative_path: str = "pw.out",
        stderr_relative_path: str = "pw.err",
    ) -> QeVcRelaxData:
        """Extract native streams and, when supplied, the final QEXSD structure."""
        streams = QePwCapturedStreamDataExtractor().extract(
            stdout_payload=stdout_payload,
            stderr_payload=stderr_payload,
            stdout_relative_path=stdout_relative_path,
            stderr_relative_path=stderr_relative_path,
        )
        final_structure = (
            QeQexsdFinalStructureExtractor().extract(qexsd_document)
            if qexsd_document is not None
            else None
        )
        return QeVcRelaxData(streams=streams, final_structure=final_structure)
