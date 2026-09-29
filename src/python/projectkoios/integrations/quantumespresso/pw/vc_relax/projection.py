"""Project calculator-neutral requests into QE ``vc-relax`` input."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.integrations.quantumespresso.pw.inputfile.cell import (
    QeCellDegreesOfFreedom,
    QeCellDynamics,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.ions import (
    QeIonDynamics,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.options import (
    QeLatticeVectorRelaxationOptions,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.projection import (  # noqa: E501
    QeRelaxationInputProjection,
    project_relaxation_input,
)
from projectkoios.integrations.quantumespresso.pw.vc_relax.configuration import (  # noqa: E501
    QeVcRelaxProjectionConfiguration,
)
from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftRelaxationRequest,
    PwDftRelaxationScope,
)


@dataclass(frozen=True, slots=True)
class QeVcRelaxInputProjector:
    """Render variable-cell relaxation with explicit ``&CELL`` controls."""

    configuration: QeVcRelaxProjectionConfiguration

    def __post_init__(self) -> None:
        if type(self.configuration) is not QeVcRelaxProjectionConfiguration:
            raise TypeError("configuration must be a QeVcRelaxProjectionConfiguration")

    def project(self, request: PwDftRelaxationRequest) -> QeRelaxationInputProjection:
        """Return deterministic QE ``vc-relax`` input."""
        if type(request) is not PwDftRelaxationRequest:
            raise TypeError("request must be a PwDftRelaxationRequest")
        if request.scope is not PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL:
            raise ValueError("vc-relax requires atomic-positions-and-cell scope")
        convergence = request.convergence
        if (
            convergence.target_pressure_kbar is None
            or convergence.pressure_tolerance_kbar is None
        ):
            raise ValueError("vc-relax requires target and convergence pressure")
        self._validate_native_policy()
        configuration = self.configuration
        return project_relaxation_input(
            request,
            configuration,
            calculation="vc-relax",
            lattice_vector_options=QeLatticeVectorRelaxationOptions(
                dynamics=configuration.cell_dynamics,
                degrees_of_freedom=configuration.cell_degrees_of_freedom,
                target_pressure_kbar=convergence.target_pressure_kbar,
                pressure_tolerance_kbar=convergence.pressure_tolerance_kbar,
            ),
        )

    def _validate_native_policy(self) -> None:
        configuration = self.configuration
        configuration.cell_dynamics.require_implemented()
        if configuration.ion_dynamics is QeIonDynamics.FIRE:
            raise ValueError("ion_dynamics='fire' is invalid for vc-relax")
        if configuration.cell_dynamics is QeCellDynamics.NONE:
            raise ValueError("cell_dynamics='none' does not relax the requested cell")
        if configuration.cell_degrees_of_freedom is QeCellDegreesOfFreedom.IBRAV:
            raise ValueError("cell_dofree='ibrav' is incompatible with ibrav=0")
        valid_pairs = {
            QeCellDynamics.BFGS: QeIonDynamics.BFGS,
            QeCellDynamics.DAMPED_PARRINELLO_RAHMAN: QeIonDynamics.DAMP,
            QeCellDynamics.DAMPED_WENTZCOVITCH: QeIonDynamics.DAMP,
        }
        if (
            valid_pairs.get(configuration.cell_dynamics)
            is not configuration.ion_dynamics
        ):
            raise ValueError("QE ion and cell dynamics declarations are incompatible")
