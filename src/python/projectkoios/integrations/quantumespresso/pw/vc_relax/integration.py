"""Quantum ESPRESSO variable-cell relaxation integration."""

from __future__ import annotations

from dataclasses import dataclass, replace

from projectkoios.integrations.quantumespresso.pw.relaxation.projection import (  # noqa: E501
    QeRelaxationInputProjection,
)
from projectkoios.integrations.quantumespresso.pw.vc_relax.configuration import (  # noqa: E501
    QeVcRelaxProjectionConfiguration,
)
from projectkoios.integrations.quantumespresso.pw.vc_relax.projection import (  # noqa: E501
    QeVcRelaxInputProjector,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.relaxation.base import PwDftRelaxationScope
from projectkoios.simulations.dft.pw.relaxation.capabilities import (
    PW_DFT_RELAXATION_BACKEND_DESCRIPTIONS,
    PwDftRelaxationBackendDescription,
)
from projectkoios.simulations.dft.pw.relaxation.integration import (
    PwDftRelaxationIntegration,
)
from projectkoios.simulations.dft.pw.relaxation.request import PwDftRelaxationRequest
from projectkoios.simulations.structure import StructureResolution


@dataclass(frozen=True, slots=True)
class QePwVcRelaxIntegration(PwDftRelaxationIntegration):
    """Implement the calculator-neutral variable-cell relaxation contract."""

    configuration: QeVcRelaxProjectionConfiguration

    def __post_init__(self) -> None:
        if type(self.configuration) is not QeVcRelaxProjectionConfiguration:
            raise TypeError("configuration must be a QeVcRelaxProjectionConfiguration")

    @property
    def description(self) -> PwDftRelaxationBackendDescription:
        """Return the reviewed QE backend description."""
        matches = tuple(
            item
            for item in PW_DFT_RELAXATION_BACKEND_DESCRIPTIONS
            if item.integration_id == CalculatorIntegrationId("quantum-espresso")
        )
        if len(matches) != 1:
            raise RuntimeError("QE relaxation backend description is not unique")
        return replace(
            matches[0],
            supported_scopes=(PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL,),
        )

    def project(
        self,
        request: PwDftRelaxationRequest,
        structure: StructureResolution,
    ) -> QeRelaxationInputProjection:
        """Return deterministic variable-cell QE input."""
        return QeVcRelaxInputProjector(self.configuration).project(request, structure)
