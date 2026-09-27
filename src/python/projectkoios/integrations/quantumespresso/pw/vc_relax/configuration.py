"""QE-native input policy for variable-cell ``vc-relax`` calculations."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.integrations.quantumespresso.pw.inputfile.cell import (
    QeCellDegreesOfFreedom,
    QeCellDynamics,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.configuration import (  # noqa: E501
    QeRelaxationInputConfiguration,
)


@dataclass(frozen=True, slots=True)
class QeVcRelaxProjectionConfiguration(QeRelaxationInputConfiguration):
    """Declare native choices for variable-cell relaxation."""

    cell_dynamics: QeCellDynamics
    cell_degrees_of_freedom: QeCellDegreesOfFreedom

    def __post_init__(self) -> None:
        super(QeVcRelaxProjectionConfiguration, self).__post_init__()
        if type(self.cell_dynamics) is not QeCellDynamics:
            raise TypeError("cell_dynamics must be a QeCellDynamics")
        if type(self.cell_degrees_of_freedom) is not QeCellDegreesOfFreedom:
            raise TypeError("cell_degrees_of_freedom must be a QeCellDegreesOfFreedom")
