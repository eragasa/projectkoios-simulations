"""Project shared calculation modes into qualified VASP INCAR assignments."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.integrations.vasp.ibrion import VaspIbrion
from projectkoios.integrations.vasp.incar import (
    IncarAssignment,
    IncarFile,
)
from projectkoios.simulations.dft.pw.settings import (
    AlignmentKind,
    CalculationType,
)
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation

IBRION_DOCUMENTATION_URL = "https://vasp.at/wiki/IBRION"
ICHARG_DOCUMENTATION_URL = "https://vasp.at/wiki/ICHARG"
ISIF_DOCUMENTATION_URL = "https://vasp.at/wiki/ISIF"
NSW_DOCUMENTATION_URL = "https://vasp.at/wiki/NSW"


@dataclass(frozen=True, slots=True)
class VaspCalculationProjection:
    """Return projected INCAR fields with fidelity and unresolved requirements."""

    input_file: IncarFile
    alignment: AlignmentKind
    required_inputs: tuple[str, ...]
    qualification: str

    def __post_init__(self) -> None:
        if type(self.input_file) is not IncarFile:
            raise TypeError("input_file must be an IncarFile")
        if type(self.alignment) is not AlignmentKind:
            raise TypeError("alignment must be an AlignmentKind")
        if type(self.required_inputs) is not tuple:
            raise TypeError("required_inputs must be a tuple")
        if any(
            type(required_input) is not str or not required_input
            for required_input in self.required_inputs
        ):
            raise ValueError("required_inputs must contain nonempty strings")
        if (
            type(self.qualification) is not str
            or not self.qualification
            or self.qualification != self.qualification.strip()
        ):
            raise ValueError("qualification must be nonempty and stripped")

    @property
    def is_complete(self) -> bool:
        """Return whether this calculation-mode projection has no open requirements."""
        return not self.required_inputs


@dataclass(frozen=True, slots=True)
class VaspCalculationProjector:
    """Project one shared calculation type into qualified VASP controls."""

    def project(self, simulation: PwDftSimulation) -> VaspCalculationProjection:
        """Return deterministic INCAR fields without concealing missing policy."""
        if type(simulation) is not PwDftSimulation:
            raise TypeError("simulation must be a PwDftSimulation")
        assignments, alignment, required_inputs, qualification = _PROJECTIONS[
            simulation.settings.calculation_type
        ]
        return VaspCalculationProjection(
            input_file=IncarFile(
                assignments=tuple(
                    IncarAssignment(tag=tag, value=value) for tag, value in assignments
                )
            ),
            alignment=alignment,
            required_inputs=required_inputs,
            qualification=qualification,
        )


_ProjectionDefinition = tuple[
    tuple[tuple[str, str], ...], AlignmentKind, tuple[str, ...], str
]
_PROJECTIONS: dict[CalculationType, _ProjectionDefinition] = {
    CalculationType.scf: (
        (("IBRION", str(VaspIbrion.no_update.value)), ("NSW", "0")),
        AlignmentKind.conditional,
        (),
        (
            "This selects a static ionic calculation; electronic, k-point, and restart "
            "settings still determine the complete VASP calculation."
        ),
    ),
    CalculationType.nscf: (
        (
            ("IBRION", str(VaspIbrion.no_update.value)),
            ("NSW", "0"),
            ("ICHARG", "11"),
        ),
        AlignmentKind.conditional,
        ("self-consistent CHGCAR",),
        (
            "ICHARG=11 keeps the charge density fixed and requires a compatible "
            "self-consistent CHGCAR from an earlier calculation."
        ),
    ),
    CalculationType.bands: (
        (
            ("IBRION", str(VaspIbrion.no_update.value)),
            ("NSW", "0"),
            ("ICHARG", "11"),
        ),
        AlignmentKind.conditional,
        ("self-consistent CHGCAR", "band-path KPOINTS"),
        (
            "A VASP band calculation requires both a compatible self-consistent "
            "CHGCAR and an independently specified band-path KPOINTS file."
        ),
    ),
    CalculationType.relax: (
        (
            ("IBRION", str(VaspIbrion.conjugate_gradient.value)),
            ("ISIF", "2"),
        ),
        AlignmentKind.approximate,
        ("INCAR.NSW",),
        (
            "IBRION=2 selects conjugate-gradient optimization and ISIF=2 varies ionic "
            "positions only; the operator must choose the ionic-step budget."
        ),
    ),
    CalculationType.md: (
        (("IBRION", str(VaspIbrion.molecular_dynamics.value)),),
        AlignmentKind.conditional,
        (
            "INCAR.NSW",
            "INCAR.POTIM",
            "VASP molecular-dynamics ensemble policy",
        ),
        (
            "IBRION=0 selects molecular dynamics but does not choose its duration, "
            "time step, integrator, thermostat, or ensemble."
        ),
    ),
    CalculationType.vc_relax: (
        (
            ("IBRION", str(VaspIbrion.conjugate_gradient.value)),
            ("ISIF", "3"),
        ),
        AlignmentKind.approximate,
        ("INCAR.NSW",),
        (
            "IBRION=2 and ISIF=3 vary positions, cell shape, and volume; the operator "
            "must choose the ionic-step budget and convergence policy."
        ),
    ),
    CalculationType.vc_md: (
        (
            ("IBRION", str(VaspIbrion.molecular_dynamics.value)),
            ("ISIF", "3"),
        ),
        AlignmentKind.conditional,
        (
            "INCAR.NSW",
            "INCAR.POTIM",
            "VASP variable-cell molecular-dynamics ensemble policy",
        ),
        (
            "IBRION=0 and ISIF=3 expose molecular dynamics with variable cell degrees "
            "of freedom but do not choose a valid ensemble or integration policy."
        ),
    ),
}
