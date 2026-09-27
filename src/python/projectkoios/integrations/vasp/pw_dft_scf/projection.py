"""Project calculator-neutral SCF intent through maintained VASP writers."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.integrations.vasp.calculation import (
    VaspCalculationProjector,
)
from projectkoios.integrations.vasp.incar import (
    IncarAssignment,
    IncarFile,
    IncarWriter,
)
from projectkoios.integrations.vasp.kpoints import (
    VaspAutomaticKpointMesh,
    VaspKpointsWriter,
)
from projectkoios.integrations.vasp.poscar import (
    PoscarModel,
    PoscarWriter,
    UnitCellModel,
)
from projectkoios.integrations.vasp.pw_dft_scf.configuration import (
    VaspScfProjectionConfiguration,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfRequest,
)
from projectkoios.simulations.dft.pw.scf.integration import (
    PwDftScfInputProjection,
    PwDftScfRenderedInput,
)
from projectkoios.simulations.dft.pw.settings import CalculationType

VASP_SCF_INTEGRATION_ID = CalculatorIntegrationId("vasp")


@dataclass(frozen=True, slots=True)
class VaspScfInputProjector:
    """Compose existing INCAR, KPOINTS, POSCAR, and calculation projectors."""

    configuration: VaspScfProjectionConfiguration

    def project(self, request: PwDftScfRequest) -> PwDftScfInputProjection:
        """Return deterministic text inputs while leaving POTCAR external."""
        if type(request) is not PwDftScfRequest:
            raise TypeError("request must be a PwDftScfRequest")
        if request.simulation.settings.calculation_type is not CalculationType.scf:
            raise ValueError("VASP SCF integration requires CalculationType.scf")
        calculation = VaspCalculationProjector().project(request.simulation)
        config = self.configuration
        incar = IncarFile(
            assignments=(
                IncarAssignment("SYSTEM", config.system_label),
                IncarAssignment("ISTART", "0"),
                IncarAssignment("ICHARG", "2"),
                IncarAssignment(
                    "ENCUT",
                    _format_float(request.sampling.wavefunction_cutoff_ev),
                ),
                IncarAssignment("ALGO", config.algorithm),
                IncarAssignment("NELM", str(config.maximum_electronic_steps)),
                IncarAssignment("EDIFF", _format_float(config.electronic_tolerance_ev)),
                IncarAssignment("ISMEAR", str(config.smearing_method)),
                IncarAssignment("SIGMA", _format_float(config.smearing_width_ev)),
                IncarAssignment("ISPIN", str(config.spin_polarization)),
                IncarAssignment(
                    "LREAL",
                    ".TRUE." if config.real_space_projection else ".FALSE.",
                ),
                *calculation.input_file.assignments,
            )
        )
        poscar = PoscarModel(
            comment=config.poscar_comment,
            unit_cell_model=UnitCellModel(request.simulation.unit_cell),
        )
        kpoints = VaspAutomaticKpointMesh(
            mesh=request.sampling.kpoint_mesh,
            shift=request.sampling.kpoint_shift,
        )
        return PwDftScfInputProjection(
            integration_id=VASP_SCF_INTEGRATION_ID,
            rendered_inputs=(
                PwDftScfRenderedInput("INCAR", IncarWriter().render(incar)),
                PwDftScfRenderedInput("KPOINTS", VaspKpointsWriter().render(kpoints)),
                PwDftScfRenderedInput("POSCAR", PoscarWriter().render(poscar)),
            ),
            required_external_inputs=("POTCAR",),
            qualification=calculation.qualification,
        )


def _format_float(value: float) -> str:
    return f"{value:.12g}".replace("e-0", "e-").replace("e+0", "e+")
