"""Compose maintained QE NSCF projection and native-data extraction."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.integrations.quantumespresso.pw.nscf.configuration import (
    QeNscfProjectionConfiguration,
)
from projectkoios.integrations.quantumespresso.pw.nscf.data_extraction import (
    QeNscfData,
    QeNscfDataExtractor,
)
from projectkoios.integrations.quantumespresso.pw.nscf.projection import (
    QeNscfInputProjection,
    QeNscfInputProjector,
)
from projectkoios.simulations.execution import CalculatorExecutionRecord
from projectkoios.simulations.structure import StructureResolution


@dataclass(frozen=True, slots=True)
class QeNscfIntegration:
    """Project and extract one NSCF calculation without workflow ownership."""

    projection_configuration: QeNscfProjectionConfiguration

    def __post_init__(self) -> None:
        if type(self.projection_configuration) is not QeNscfProjectionConfiguration:
            raise TypeError(
                "projection_configuration must be a QeNscfProjectionConfiguration"
            )

    def project(self, structure: StructureResolution) -> QeNscfInputProjection:
        """Project an exact resolved structure into typed QE cards."""
        return QeNscfInputProjector(self.projection_configuration).project(structure)

    def extract(
        self,
        *,
        stdout_payload: bytes,
        stderr_payload: bytes,
        qexsd_document: object,
        execution: CalculatorExecutionRecord | None = None,
    ) -> QeNscfData:
        """Extract native NSCF evidence against the configured dimensions."""
        return QeNscfDataExtractor().extract(
            stdout_payload=stdout_payload,
            stderr_payload=stderr_payload,
            qexsd_document=qexsd_document,
            expected_band_count=self.projection_configuration.band_count,
            expected_kpoint_count=len(self.projection_configuration.kpoints),
            execution=execution,
        )
