"""Shared component assembly for ``relax`` and ``vc-relax`` consumers."""

from __future__ import annotations

from typing import Literal

import numpy as np
from numpy.typing import NDArray
from physkit.units import MODEL_SYSTEM_UNIT_CONVERTER, PhysicalUnit

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeAtomicPositionsCard,
    QeAtomicSpeciesCard,
    QeCard,
    QeCellParametersCard,
    QeControlCard,
    QeElectronsCard,
    QeIonsCard,
    QeKpointsCard,
    QeSystemCard,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.configuration import (  # noqa: E501
    QeRelaxationInputConfiguration,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.model import (
    PwInput,
    PwInputWriter,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftRelaxationRequest,
)
from projectkoios.simulations.dft.pw.relaxation.integration import (
    PwDftRelaxationInputProjection,
    PwDftRelaxationRenderedInput,
)


def project_relaxation_input(
    request: PwDftRelaxationRequest,
    configuration: QeRelaxationInputConfiguration,
    *,
    calculation: Literal["relax", "vc-relax"],
    cell_component: QeCard | None,
) -> PwDftRelaxationInputProjection:
    """Assemble one relaxation mode from the authoritative component vocabulary."""
    if type(request) is not PwDftRelaxationRequest:
        raise TypeError("request must be a PwDftRelaxationRequest")
    if not isinstance(configuration, QeRelaxationInputConfiguration):
        raise TypeError("configuration must be a QeRelaxationInputConfiguration")
    if calculation not in ("relax", "vc-relax"):
        raise ValueError("calculation must be relax or vc-relax")
    atoms = request.simulation.unit_cell.atomic_basis.atoms
    if {atom.symbol for atom in atoms} != {
        item.symbol for item in configuration.species
    }:
        raise ValueError("QE species must exactly match the unit cell")
    cutoff_ry = request.sampling.wavefunction_cutoff_ev * _conversion_factor("eV", "Ry")
    convergence = request.convergence
    energy_tolerance_ry = convergence.total_energy_tolerance_ev * _conversion_factor(
        "eV", "Ry"
    )
    force_tolerance_ry_per_bohr = (
        convergence.force_tolerance_ev_per_angstrom
        * _conversion_factor("eV/angstrom", "Ry/bohr")
    )
    components: list[QeCard] = [
        QeControlCard(
            lines=(
                f"calculation = '{calculation}'",
                f"nstep = {convergence.maximum_ionic_steps}",
                f"etot_conv_thr = {energy_tolerance_ry:.10e}",
                f"forc_conv_thr = {force_tolerance_ry_per_bohr:.10e}",
                "tprnfor = .true.",
                f"tstress = {'.true.' if calculation == 'vc-relax' else '.false.'}",
                f"prefix = '{configuration.prefix}'",
                f"pseudo_dir = '{configuration.pseudo_dir}'",
                f"outdir = '{configuration.outdir}'",
            )
        ),
        QeSystemCard(
            lines=(
                "ibrav = 0",
                f"nat = {len(atoms)}",
                f"ntyp = {len(configuration.species)}",
                f"ecutwfc = {cutoff_ry:.10f}",
                "ecutrho = "
                f"{cutoff_ry * configuration.charge_density_cutoff_ratio:.10f}",
            )
        ),
        QeElectronsCard(
            lines=(f"conv_thr = {configuration.electronic_tolerance_ry:.10e}",)
        ),
        QeIonsCard(lines=(f"ion_dynamics = '{configuration.ion_dynamics.value}'",)),
    ]
    if cell_component is not None:
        components.append(cell_component)
    components.extend(
        (
            QeAtomicSpeciesCard(
                lines=tuple(
                    f"{item.symbol} {item.mass_amu:.10g} "
                    f"{item.pseudopotential_filename}"
                    for item in configuration.species
                )
            ),
            QeKpointsCard(
                option="automatic",
                lines=(
                    " ".join(
                        str(value)
                        for value in (
                            *request.sampling.kpoint_mesh,
                            *request.sampling.kpoint_shift,
                        )
                    ),
                ),
            ),
        )
    )
    unit_cell = request.simulation.unit_cell
    length_factor = MODEL_SYSTEM_UNIT_CONVERTER.conversion_factor(
        unit_cell.H.unit,
        PhysicalUnit("angstrom"),
    )
    precision = configuration.coordinate_precision
    components.extend(
        (
            QeCellParametersCard(
                option="(angstrom)",
                lines=tuple(
                    _format_vector(
                        unit_cell.H.magnitude[:, index] * length_factor, precision
                    )
                    for index in range(3)
                ),
            ),
            QeAtomicPositionsCard(
                option="(crystal)",
                lines=tuple(
                    f"{atom.symbol} "
                    f"{_format_vector(atom.position_fractional.magnitude, precision)}"
                    for atom in atoms
                ),
            ),
        )
    )
    card_order = {
        "ATOMIC_SPECIES": 0,
        "CELL_PARAMETERS": 1,
        "ATOMIC_POSITIONS": 2,
        "K_POINTS": 3,
    }
    groups = tuple(component.to_input_group() for component in components)
    namelists = tuple(group for group in groups if group.kind == "namelist")
    cards = tuple(
        sorted(
            (group for group in groups if group.kind == "card"),
            key=lambda group: card_order[group.tag.split(maxsplit=1)[0]],
        )
    )
    input_file = PwInput(groups=(*namelists, *cards))
    return PwDftRelaxationInputProjection(
        integration_id=CalculatorIntegrationId("quantum-espresso"),
        rendered_inputs=(
            PwDftRelaxationRenderedInput(
                filename=configuration.input_filename,
                text=PwInputWriter().render(input_file),
            ),
        ),
        required_external_inputs=tuple(
            item.pseudopotential_filename for item in configuration.species
        ),
        qualification=(
            "QE 7.5 component-based projection. Native optimizer and cell controls "
            "remain QE-specific and do not establish cross-code equivalence."
        ),
    )


def _conversion_factor(source: str, target: str) -> float:
    return MODEL_SYSTEM_UNIT_CONVERTER.conversion_factor(
        PhysicalUnit(source), PhysicalUnit(target)
    )


def _format_vector(values: NDArray[np.float64], precision: int) -> str:
    first, second, third = values
    return " ".join(f"{float(value):.{precision}f}" for value in (first, second, third))
