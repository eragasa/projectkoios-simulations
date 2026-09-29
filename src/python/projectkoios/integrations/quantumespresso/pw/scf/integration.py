"""Quantum ESPRESSO implementation of the common SCF integration contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.quantumespresso.pw.scf import (
    configuration as qe_configuration,
)
from projectkoios.integrations.quantumespresso.pw.scf import (
    data_extraction as qe_data_extraction,
)
from projectkoios.integrations.quantumespresso.pw.scf import (
    projection as qe_projection,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfObservation,
    PwDftScfRequest,
)
from projectkoios.simulations.dft.pw.scf.integration import (
    PwDftScfInputProjection,
    PwDftScfIntegration,
)


@dataclass(frozen=True, slots=True)
class QePwDftScfIntegration(PwDftScfIntegration):
    """Compose maintained QE projection and retained-data extraction."""

    artifact_root: Path
    projection_configuration: qe_configuration.QeScfProjectionConfiguration

    def __post_init__(self) -> None:
        if not self.artifact_root.is_dir() or self.artifact_root.is_symlink():
            raise ValueError("artifact_root must be an existing nonsymlink directory")
        if (
            type(self.projection_configuration)
            is not qe_configuration.QeScfProjectionConfiguration
        ):
            raise TypeError(
                "projection_configuration must be a QeScfProjectionConfiguration"
            )

    @property
    def integration_id(self) -> CalculatorIntegrationId:
        """Return the stable Quantum ESPRESSO backend identity."""
        return qe_projection.QE_SCF_INTEGRATION_ID

    def project(self, request: PwDftScfRequest) -> PwDftScfInputProjection:
        """Project common intent through the maintained QE input assembler."""
        return qe_projection.QeScfInputProjector(
            configuration=self.projection_configuration
        ).project(request)

    def analyze(self, output_artifact_id: str) -> PwDftScfObservation:
        """Normalize one retained successful ``pw.x`` observation."""
        return (
            qe_data_extraction.QeScfDataExtractor(artifact_root=self.artifact_root)
            .extract(output_artifact_id)
            .observation
        )
