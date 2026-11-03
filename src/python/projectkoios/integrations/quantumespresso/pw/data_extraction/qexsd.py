"""Common facade over a supplied parsed QEXSD document record."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.integrations.quantumespresso.pw.relaxation.structure import (
    QexsdFinalStructure,
    QexsdFinalStructureExtractor,
)
from projectkoios.integrations.quantumespresso.qexsd.records import QexsdDocument


@dataclass(frozen=True, slots=True)
class QexsdData:
    """Retain a parsed QEXSD document and its interpreted final structure."""

    document: QexsdDocument
    final_structure: QexsdFinalStructure

    def __post_init__(self) -> None:
        if type(self.document) is not QexsdDocument:
            raise TypeError("document must be a QexsdDocument")
        if type(self.final_structure) is not QexsdFinalStructure:
            raise TypeError("final_structure must be QexsdFinalStructure")
        for document_name, structure_value in (
            ("source_path", self.final_structure.source_path),
            ("source_sha256", self.final_structure.source_sha256),
            ("source_byte_count", self.final_structure.source_byte_count),
            ("qexsd_version", self.final_structure.qexsd_version),
            ("exit_status", self.final_structure.exit_status),
        ):
            if getattr(self.document, document_name) != structure_value:
                raise ValueError(
                    f"QEXSD document and final structure disagree on {document_name}"
                )

    @classmethod
    def from_document(cls, document: QexsdDocument) -> QexsdData:
        """Interpret the final structure while retaining the supplied document."""
        return cls(
            document=document,
            final_structure=QexsdFinalStructureExtractor(document).extract(),
        )
