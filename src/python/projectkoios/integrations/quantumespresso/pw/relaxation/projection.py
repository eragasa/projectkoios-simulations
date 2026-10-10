"""Shared component assembly for ``relax`` and ``vc-relax`` consumers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeAtomicPositionsCard,
    QeAtomicSpeciesCard,
    QeCard,
    QeCellCard,
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
from projectkoios.integrations.quantumespresso.pw.relaxation.options import (
    QeIonicRelaxationOptions,
    QeLatticeVectorRelaxationOptions,
)
from projectkoios.physkit.units import MODEL_SYSTEM_UNIT_CONVERTER, PhysicalUnit
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.electronic import DftSpinMode
from projectkoios.simulations.dft.pseudopotential import (
    PseudopotentialArtifactFormat,
)
from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftRelaxationRequest,
)
from projectkoios.simulations.dft.pw.relaxation.integration import (
    PwDftRelaxationInputProjection,
    PwDftRelaxationRenderedInput,
)


@dataclass(frozen=True, slots=True)
class QeRelaxationInputProjection(PwDftRelaxationInputProjection):
    """Retain common QE cards inside an explicitly relaxation-owned result."""

    calculation: Literal["relax", "vc-relax"]
    ionic_options: QeIonicRelaxationOptions
    lattice_vector_options: QeLatticeVectorRelaxationOptions | None
    control_card: QeControlCard
    system_card: QeSystemCard
    electrons_card: QeElectronsCard
    ions_card: QeIonsCard
    cell_card: QeCellCard | None
    atomic_species_card: QeAtomicSpeciesCard
    kpoints_card: QeKpointsCard
    cell_parameters_card: QeCellParametersCard
    atomic_positions_card: QeAtomicPositionsCard

    def __post_init__(self) -> None:
        super(QeRelaxationInputProjection, self).__post_init__()
        if self.calculation not in ("relax", "vc-relax"):
            raise ValueError("calculation must be relax or vc-relax")
        if type(self.ionic_options) is not QeIonicRelaxationOptions:
            raise TypeError("ionic_options must be a QeIonicRelaxationOptions")
        for label, value, expected_type in (
            ("control_card", self.control_card, QeControlCard),
            ("system_card", self.system_card, QeSystemCard),
            ("electrons_card", self.electrons_card, QeElectronsCard),
            ("ions_card", self.ions_card, QeIonsCard),
            ("atomic_species_card", self.atomic_species_card, QeAtomicSpeciesCard),
            ("kpoints_card", self.kpoints_card, QeKpointsCard),
            ("cell_parameters_card", self.cell_parameters_card, QeCellParametersCard),
            (
                "atomic_positions_card",
                self.atomic_positions_card,
                QeAtomicPositionsCard,
            ),
        ):
            if type(value) is not expected_type:
                raise TypeError(f"{label} must be a {expected_type.__name__}")
        if self.calculation == "relax":
            if self.lattice_vector_options is not None or self.cell_card is not None:
                raise ValueError(
                    "relax must not contain lattice-vector options or a cell card"
                )
        elif (
            type(self.lattice_vector_options) is not QeLatticeVectorRelaxationOptions
            or type(self.cell_card) is not QeCellCard
        ):
            raise TypeError("vc-relax requires lattice-vector options and a QeCellCard")


def project_relaxation_input(
    request: PwDftRelaxationRequest,
    configuration: QeRelaxationInputConfiguration,
    *,
    calculation: Literal["relax", "vc-relax"],
    lattice_vector_options: QeLatticeVectorRelaxationOptions | None,
) -> QeRelaxationInputProjection:
    """Assemble one relaxation mode from the authoritative component vocabulary."""
    if type(request) is not PwDftRelaxationRequest:
        raise TypeError("request must be a PwDftRelaxationRequest")
    if not isinstance(configuration, QeRelaxationInputConfiguration):
        raise TypeError("configuration must be a QeRelaxationInputConfiguration")
    if calculation not in ("relax", "vc-relax"):
        raise ValueError("calculation must be relax or vc-relax")
    if calculation == "relax" and lattice_vector_options is not None:
        raise ValueError("relax must not declare lattice-vector options")
    if calculation == "vc-relax" and (
        type(lattice_vector_options) is not QeLatticeVectorRelaxationOptions
    ):
        raise TypeError("vc-relax requires lattice-vector relaxation options")
    atoms = request.simulation.unit_cell.atomic_basis.atoms
    if {atom.symbol for atom in atoms} != {
        item.symbol for item in configuration.species
    }:
        raise ValueError("QE species must exactly match the unit cell")
    if request.simulation.pseudopotentials:
        if any(
            item.artifact_format is not PseudopotentialArtifactFormat.UPF
            for item in request.simulation.pseudopotentials
        ):
            raise ValueError("QE translation requires UPF pseudopotentials")
        configured_filenames = {
            item.symbol: item.pseudopotential_filename for item in configuration.species
        }
        bound_filenames = {
            item.symbol: item.filename for item in request.simulation.pseudopotentials
        }
        if configured_filenames != bound_filenames:
            raise ValueError(
                "QE configuration must match exact bound pseudopotential filenames"
            )
    if request.simulation.spin.mode not in {
        DftSpinMode.UNPOLARIZED,
        DftSpinMode.COLLINEAR,
    }:
        raise NotImplementedError(
            "QE relaxation translation supports only unpolarized and collinear spin"
        )
    if request.simulation.spin.initial_site_magnetic_moments_mu_b:
        raise NotImplementedError(
            "QE relaxation translation of site-resolved initial moments is not "
            "implemented"
        )
    cutoff_ry = request.sampling.wavefunction_cutoff_ev * _conversion_factor("eV", "Ry")
    convergence = request.convergence
    energy_tolerance_ry = convergence.total_energy_tolerance_ev * _conversion_factor(
        "eV", "Ry"
    )
    force_tolerance_ry_per_bohr = (
        convergence.force_tolerance_ev_per_angstrom
        * _conversion_factor("eV/angstrom", "Ry/bohr")
    )
    ionic_options = QeIonicRelaxationOptions(
        dynamics=configuration.ion_dynamics,
        maximum_steps=convergence.maximum_ionic_steps,
        total_energy_tolerance_ry=energy_tolerance_ry,
        force_tolerance_ry_per_bohr=force_tolerance_ry_per_bohr,
    )
    control_card = _build_relaxation_control_card(
        calculation=calculation,
        configuration=configuration,
        ionic_options=ionic_options,
    )
    system_card = _build_relaxation_system_card(
        atom_count=len(atoms),
        species_count=len(configuration.species),
        wavefunction_cutoff_ry=cutoff_ry,
        charge_density_cutoff_ratio=configuration.charge_density_cutoff_ratio,
        charge_state=request.simulation.charge.charge_state,
        spin_mode=request.simulation.spin.mode,
        constrain_spin_channel_difference=(
            request.simulation.spin.constrain_spin_channel_difference
        ),
        spin_channel_electron_difference=(
            request.simulation.spin.spin_channel_electron_difference
        ),
    )
    electrons_card = _build_relaxation_electrons_card(
        configuration.electronic_tolerance_ry
    )
    ions_card = _build_relaxation_ions_card(ionic_options)
    cell_card = (
        None
        if lattice_vector_options is None
        else _build_lattice_vector_relaxation_card(lattice_vector_options)
    )
    atomic_species_card = _build_relaxation_atomic_species_card(configuration)
    kpoints_card = _build_relaxation_kpoints_card(request)
    cell_parameters_card = _build_relaxation_cell_parameters_card(
        request,
        precision=configuration.coordinate_precision,
    )
    atomic_positions_card = _build_relaxation_atomic_positions_card(
        request,
        precision=configuration.coordinate_precision,
    )
    components: list[QeCard] = [
        control_card,
        system_card,
        electrons_card,
        ions_card,
    ]
    if cell_card is not None:
        components.append(cell_card)
    components.extend(
        (
            atomic_species_card,
            kpoints_card,
            cell_parameters_card,
            atomic_positions_card,
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
    return QeRelaxationInputProjection(
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
        calculation=calculation,
        ionic_options=ionic_options,
        lattice_vector_options=lattice_vector_options,
        control_card=control_card,
        system_card=system_card,
        electrons_card=electrons_card,
        ions_card=ions_card,
        cell_card=cell_card,
        atomic_species_card=atomic_species_card,
        kpoints_card=kpoints_card,
        cell_parameters_card=cell_parameters_card,
        atomic_positions_card=atomic_positions_card,
    )


def _build_relaxation_control_card(
    *,
    calculation: Literal["relax", "vc-relax"],
    configuration: QeRelaxationInputConfiguration,
    ionic_options: QeIonicRelaxationOptions,
) -> QeControlCard:
    return QeControlCard(
        lines=(
            f"calculation = '{calculation}'",
            f"nstep = {ionic_options.maximum_steps}",
            f"etot_conv_thr = {ionic_options.total_energy_tolerance_ry:.10e}",
            f"forc_conv_thr = {ionic_options.force_tolerance_ry_per_bohr:.10e}",
            "tprnfor = .true.",
            f"tstress = {'.true.' if calculation == 'vc-relax' else '.false.'}",
            f"prefix = '{configuration.prefix}'",
            f"pseudo_dir = '{configuration.pseudo_dir}'",
            f"outdir = '{configuration.outdir}'",
        )
    )


def _build_relaxation_system_card(
    *,
    atom_count: int,
    species_count: int,
    wavefunction_cutoff_ry: float,
    charge_density_cutoff_ratio: float,
    charge_state: int,
    spin_mode: DftSpinMode,
    constrain_spin_channel_difference: bool,
    spin_channel_electron_difference: int,
) -> QeSystemCard:
    electronic_lines: tuple[str, ...] = ()
    if charge_state != 0:
        electronic_lines += (f"tot_charge = {charge_state}",)
    if spin_mode is DftSpinMode.COLLINEAR:
        electronic_lines += ("nspin = 2",)
        if constrain_spin_channel_difference:
            electronic_lines += (
                f"tot_magnetization = {spin_channel_electron_difference}",
            )
    return QeSystemCard(
        lines=(
            "ibrav = 0",
            f"nat = {atom_count}",
            f"ntyp = {species_count}",
            f"ecutwfc = {wavefunction_cutoff_ry:.10f}",
            f"ecutrho = {wavefunction_cutoff_ry * charge_density_cutoff_ratio:.10f}",
            *electronic_lines,
        )
    )


def _build_relaxation_electrons_card(tolerance_ry: float) -> QeElectronsCard:
    return QeElectronsCard(lines=(f"conv_thr = {tolerance_ry:.10e}",))


def _build_relaxation_ions_card(
    options: QeIonicRelaxationOptions,
) -> QeIonsCard:
    return QeIonsCard(lines=(f"ion_dynamics = '{options.dynamics.value}'",))


def _build_lattice_vector_relaxation_card(
    options: QeLatticeVectorRelaxationOptions,
) -> QeCellCard:
    return QeCellCard(
        lines=(
            f"cell_dynamics = '{options.dynamics.value}'",
            f"press = {options.target_pressure_kbar:.10f}",
            f"press_conv_thr = {options.pressure_tolerance_kbar:.10f}",
            f"cell_dofree = '{options.degrees_of_freedom.value}'",
        )
    )


def _build_relaxation_atomic_species_card(
    configuration: QeRelaxationInputConfiguration,
) -> QeAtomicSpeciesCard:
    return QeAtomicSpeciesCard(
        lines=tuple(
            f"{item.symbol} {item.mass_amu:.10g} {item.pseudopotential_filename}"
            for item in configuration.species
        )
    )


def _build_relaxation_kpoints_card(
    request: PwDftRelaxationRequest,
) -> QeKpointsCard:
    return QeKpointsCard(
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
    )


def _build_relaxation_cell_parameters_card(
    request: PwDftRelaxationRequest,
    *,
    precision: int,
) -> QeCellParametersCard:
    unit_cell = request.simulation.unit_cell
    length_factor = MODEL_SYSTEM_UNIT_CONVERTER.conversion_factor(
        unit_cell.H.unit,
        PhysicalUnit("angstrom"),
    )
    return QeCellParametersCard(
        option="(angstrom)",
        lines=tuple(
            _format_vector(unit_cell.H.magnitude[:, index] * length_factor, precision)
            for index in range(3)
        ),
    )


def _build_relaxation_atomic_positions_card(
    request: PwDftRelaxationRequest,
    *,
    precision: int,
) -> QeAtomicPositionsCard:
    return QeAtomicPositionsCard(
        option="(crystal)",
        lines=tuple(
            f"{atom.symbol} "
            f"{_format_vector(atom.position_fractional.magnitude, precision)}"
            for atom in request.simulation.unit_cell.atomic_basis.atoms
        ),
    )


def _conversion_factor(source: str, target: str) -> float:
    return MODEL_SYSTEM_UNIT_CONVERTER.conversion_factor(
        PhysicalUnit(source), PhysicalUnit(target)
    )


def _format_vector(values: NDArray[np.float64], precision: int) -> str:
    first, second, third = values
    return " ".join(f"{float(value):.{precision}f}" for value in (first, second, third))
