"""VASP composition of the calculator-neutral SCF integration contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.vasp.pw_dft_scf.configuration import (
    VaspScfProjectionConfiguration,
)
from projectkoios.integrations.vasp.pw_dft_scf.output_analysis import (
    VaspScfOutputArtifactAnalyzer,
)
from projectkoios.integrations.vasp.pw_dft_scf.projection import (
    VASP_SCF_INTEGRATION_ID,
    VaspScfInputProjector,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator_input import CalculatorInputRecord
from projectkoios.simulations.dft.pw.scf.base import PwDftScfObservation
from projectkoios.simulations.dft.pw.scf.integration import PwDftScfIntegration
from projectkoios.simulations.dft.pw.scf.request import PwDftScfRequest
from projectkoios.simulations.structure import StructureResolution


@dataclass(frozen=True, slots=True)
class VaspScfIntegration(PwDftScfIntegration):
    """Compose maintained VASP projection and retained-output analysis."""

    artifact_root: Path
    projection_configuration: VaspScfProjectionConfiguration

    def __post_init__(self) -> None:
        if not self.artifact_root.is_dir() or self.artifact_root.is_symlink():
            raise ValueError("artifact_root must be an existing nonsymlink directory")
        if type(self.projection_configuration) is not VaspScfProjectionConfiguration:
            raise TypeError(
                "projection_configuration must be a VaspScfProjectionConfiguration"
            )

    @property
    def integration_id(self) -> CalculatorIntegrationId:
        """Return the stable VASP backend identity."""
        return VASP_SCF_INTEGRATION_ID

    def project(
        self,
        request: PwDftScfRequest,
        structure: StructureResolution,
    ) -> CalculatorInputRecord:
        """Project common intent through maintained VASP input writers."""
        # The exact record-to-bytes check is completed before VASP translation;
        # this adapter therefore receives, rather than invents, resolved geometry.
        return VaspScfInputProjector(self.projection_configuration).project(
            request, structure
        )

    def analyze(self, output_artifact_id: str) -> PwDftScfObservation:
        """Normalize one retained successful OUTCAR observation."""
        return VaspScfOutputArtifactAnalyzer(self.artifact_root).analyze(
            output_artifact_id
        )
