"""Project calculator-neutral requests into QE ``relax`` input."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.integrations.quantumespresso.pw.relax.configuration import (  # noqa: E501
    QeRelaxProjectionConfiguration,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.projection import (  # noqa: E501
    QeRelaxationInputProjection,
    project_relaxation_input,
)
from projectkoios.simulations.dft.pw.relaxation.base import PwDftRelaxationScope
from projectkoios.simulations.dft.pw.relaxation.request import PwDftRelaxationRequest
from projectkoios.simulations.structure import StructureResolution


@dataclass(frozen=True, slots=True)
class QeRelaxInputProjector:
    """Render fixed-cell ionic relaxation with no ``&CELL`` namelist."""

    configuration: QeRelaxProjectionConfiguration

    def __post_init__(self) -> None:
        if type(self.configuration) is not QeRelaxProjectionConfiguration:
            raise TypeError("configuration must be a QeRelaxProjectionConfiguration")

    def project(
        self,
        request: PwDftRelaxationRequest,
        structure: StructureResolution,
    ) -> QeRelaxationInputProjection:
        """Return deterministic QE ``relax`` input."""
        if type(request) is not PwDftRelaxationRequest:
            raise TypeError("request must be a PwDftRelaxationRequest")
        if request.specification.scope is not PwDftRelaxationScope.ATOMIC_POSITIONS:
            raise ValueError("relax requires atomic-positions-only scope")
        # The shared assembler consumes the already verified structure; this
        # provider layer never performs implicit repository lookup.
        return project_relaxation_input(
            request,
            structure,
            self.configuration,
            calculation="relax",
            lattice_vector_options=None,
        )
