"""Shared component assembly for ``relax`` and ``vc-relax`` consumers."""

from __future__ import annotations

import hashlib
import json
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
from projectkoios.simulations.calculator_input import (
    CalculatorExternalInputRequirement,
    CalculatorInputArtifact,
    CalculatorInputMapping,
    CalculatorInputRecord,
)
from projectkoios.simulations.dft.electronic import DftOccupationMethod, DftSpinMode
from projectkoios.simulations.dft.pseudopotential import (
    PseudopotentialArtifactFormat,
)
from projectkoios.simulations.dft.pw.relaxation.request import PwDftRelaxationRequest
from projectkoios.simulations.dft.pw.simulation import ResolvedPwDftSimulation
from projectkoios.simulations.library.codec import simulation_source_reference
from projectkoios.simulations.structure import StructureResolution


def project_relaxation_input(
    request: PwDftRelaxationRequest,
    structure: StructureResolution,
    configuration: QeRelaxationInputConfiguration,
    *,
    calculation: Literal["relax", "vc-relax"],
    lattice_vector_options: QeLatticeVectorRelaxationOptions | None,
) -> CalculatorInputRecord:
    """Assemble exact prepared relaxation input and dependency identities."""
    if type(request) is not PwDftRelaxationRequest:
        raise TypeError("request must be a PwDftRelaxationRequest")
    if type(structure) is not StructureResolution:
        raise TypeError("structure must be a StructureResolution")
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
    specification = request.specification
    simulation = specification.simulation
    resolved = ResolvedPwDftSimulation(simulation=simulation, structure=structure)
    atoms = resolved.unit_cell.atomic_basis.atoms
    if {atom.symbol for atom in atoms} != {
        item.symbol for item in configuration.species
    }:
        raise ValueError("QE species must exactly match the unit cell")
    if not simulation.pseudopotentials:
        raise ValueError("QE translation requires exact bound pseudopotentials")
    if any(
        item.artifact_format is not PseudopotentialArtifactFormat.UPF
        for item in simulation.pseudopotentials
    ):
        raise ValueError("QE translation requires UPF pseudopotentials")
    configured_filenames = {
        item.symbol: item.pseudopotential_filename for item in configuration.species
    }
    bound_filenames = {
        item.symbol: item.filename for item in simulation.pseudopotentials
    }
    if configured_filenames != bound_filenames:
        raise ValueError(
            "QE configuration must match exact bound pseudopotential filenames"
        )
    if simulation.spin.mode not in {
        DftSpinMode.UNPOLARIZED,
        DftSpinMode.COLLINEAR,
    }:
        raise NotImplementedError(
            "QE relaxation translation supports only unpolarized and collinear spin"
        )
    if simulation.spin.initial_site_magnetic_moments_mu_b:
        raise NotImplementedError(
            "QE relaxation translation of site-resolved initial moments is not "
            "implemented"
        )
    # Maintained QE relaxation rendering currently exposes only fixed
    # occupations; unsupported intent fails closed.
    if specification.occupation.method is not DftOccupationMethod.FIXED:
        raise NotImplementedError(
            "QE relaxation smearing translation is not implemented"
        )
    neutral_electronic_tolerance_ry = (
        specification.electronic_convergence.energy_tolerance_ev
        * _conversion_factor("eV", "Ry")
    )
    if (
        abs(neutral_electronic_tolerance_ry - configuration.electronic_tolerance_ry)
        > configuration.electronic_atol_ry
    ):
        raise ValueError(
            "QE configuration electronic tolerance must match specification"
        )

    cutoff_ry = specification.wavefunction_cutoff_ev * _conversion_factor("eV", "Ry")
    convergence = specification.ionic_convergence
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
        charge_state=simulation.charge.charge_state,
        spin_mode=simulation.spin.mode,
        constrain_spin_channel_difference=(
            simulation.spin.constrain_spin_channel_difference
        ),
        spin_channel_electron_difference=(
            simulation.spin.spin_channel_electron_difference
        ),
        use_spatial_symmetry=specification.kpoint_sampling.use_spatial_symmetry,
        use_time_reversal=specification.kpoint_sampling.use_time_reversal,
    )
    electrons_card = _build_relaxation_electrons_card(
        configuration.electronic_tolerance_ry,
        specification.electronic_convergence.maximum_electronic_iterations,
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
        resolved,
        precision=configuration.coordinate_precision,
    )
    atomic_positions_card = _build_relaxation_atomic_positions_card(
        resolved,
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
    rendered_content = PwInputWriter().render(input_file).encode("ascii")
    source = simulation_source_reference(specification)
    mesh = specification.kpoint_sampling.mesh
    shift = specification.kpoint_sampling.shift
    degrees_native_fields: list[str] = ["CONTROL.calculation"]
    degrees_native_values: list[str] = [calculation]
    if lattice_vector_options is not None:
        degrees_native_fields.extend(("CELL.cell_dynamics", "CELL.cell_dofree"))
        degrees_native_values.extend(
            (
                lattice_vector_options.dynamics.value,
                lattice_vector_options.degrees_of_freedom.value,
            )
        )
    return CalculatorInputRecord(
        input_id=(
            f"{specification.simulation_id}.QuantumEspresso.Relaxation.PreparedInput"
        ),
        schema_version=1,
        source=source,
        integration_id=CalculatorIntegrationId("quantum-espresso"),
        calculator_name="Quantum ESPRESSO pw.x",
        calculator_version_constraint=">=7.5,<8",
        representation="quantum-espresso-pw-input",
        artifacts=(
            CalculatorInputArtifact(
                role="primary-input",
                filename=configuration.input_filename,
                media_type="text/plain; charset=us-ascii",
                content=rendered_content,
                byte_size=len(rendered_content),
                sha256=hashlib.sha256(rendered_content).hexdigest(),
            ),
        ),
        external_requirements=tuple(
            CalculatorExternalInputRequirement(
                role="pseudopotential",
                stable_id=f"{item.symbol}.{item.sha256}",
                filename=item.filename,
                format=(
                    f"{item.artifact_format.value};"
                    f"version={item.artifact_format_version}"
                ),
                byte_size=item.byte_size,
                sha256=item.sha256,
                provenance=f"canonical-simulation-specification:{source.sha256}",
                element_symbol=item.symbol,
            )
            for item in simulation.pseudopotentials
        ),
        mappings=(
            CalculatorInputMapping(
                neutral_field="structure",
                neutral_value=(
                    f"{simulation.structure.structure_id}/{simulation.structure.sha256}"
                ),
                native_fields=("CELL_PARAMETERS", "ATOMIC_POSITIONS"),
                native_values=("angstrom", "crystal"),
                effect="encoding",
                qualification="Exact verified starting geometry is rendered.",
            ),
            CalculatorInputMapping(
                neutral_field="degrees_of_freedom",
                neutral_value=json.dumps(
                    {
                        "cell_mode": specification.degrees_of_freedom.cell_mode.value,
                        "relax_atomic_positions": (
                            specification.degrees_of_freedom.relax_atomic_positions
                        ),
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                native_fields=tuple(degrees_native_fields),
                native_values=tuple(degrees_native_values),
                effect="encoding",
                qualification=(
                    "QE calculation and CELL controls encode the declared scope."
                ),
            ),
            CalculatorInputMapping(
                neutral_field="wavefunction_cutoff_ev",
                neutral_value=f"{specification.wavefunction_cutoff_ev:.17g}",
                native_fields=("SYSTEM.ecutwfc", "SYSTEM.ecutrho"),
                native_values=(
                    f"{cutoff_ry:.10f}",
                    f"{cutoff_ry * configuration.charge_density_cutoff_ratio:.10f}",
                ),
                effect="unit-conversion",
                qualification="The configured density-cutoff ratio is explicit.",
            ),
            CalculatorInputMapping(
                neutral_field="occupation",
                neutral_value=json.dumps(
                    {"method": specification.occupation.method.value},
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                native_fields=("SYSTEM.occupations",),
                native_values=("fixed",),
                effect="encoding",
                qualification="Unsupported occupation families fail closed.",
            ),
            CalculatorInputMapping(
                neutral_field="kpoint_sampling",
                neutral_value=json.dumps(
                    {
                        "mesh": mesh,
                        "shift": shift,
                        "use_spatial_symmetry": (
                            specification.kpoint_sampling.use_spatial_symmetry
                        ),
                        "use_time_reversal": (
                            specification.kpoint_sampling.use_time_reversal
                        ),
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                native_fields=(
                    "K_POINTS.automatic",
                    "SYSTEM.nosym",
                    "SYSTEM.noinv",
                ),
                native_values=(
                    f"{mesh[0]} {mesh[1]} {mesh[2]} {shift[0]} {shift[1]} {shift[2]}",
                    (
                        ".false.-default"
                        if specification.kpoint_sampling.use_spatial_symmetry
                        else ".true."
                    ),
                    (
                        ".false.-default"
                        if specification.kpoint_sampling.use_time_reversal
                        else ".true."
                    ),
                ),
                effect="encoding",
                qualification="QE nosym and noinv encode disabled reductions.",
            ),
            CalculatorInputMapping(
                neutral_field="electronic_convergence",
                neutral_value=json.dumps(
                    {
                        "energy_tolerance_ev": (
                            specification.electronic_convergence.energy_tolerance_ev
                        ),
                        "maximum_electronic_iterations": (
                            specification.electronic_convergence.maximum_electronic_iterations
                        ),
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                native_fields=("ELECTRONS.conv_thr", "ELECTRONS.electron_maxstep"),
                native_values=(
                    f"{configuration.electronic_tolerance_ry:.10e}",
                    str(
                        specification.electronic_convergence.maximum_electronic_iterations
                    ),
                ),
                effect="unit-conversion",
                qualification="The eV-to-Ry threshold mapping is explicit.",
            ),
            CalculatorInputMapping(
                neutral_field="ionic_convergence",
                neutral_value=json.dumps(
                    {
                        "force_tolerance_ev_per_angstrom": (
                            convergence.force_tolerance_ev_per_angstrom
                        ),
                        "maximum_ionic_steps": convergence.maximum_ionic_steps,
                        "total_energy_tolerance_ev": (
                            convergence.total_energy_tolerance_ev
                        ),
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                native_fields=(
                    "CONTROL.nstep",
                    "CONTROL.etot_conv_thr",
                    "CONTROL.forc_conv_thr",
                ),
                native_values=(
                    str(ionic_options.maximum_steps),
                    f"{ionic_options.total_energy_tolerance_ry:.10e}",
                    f"{ionic_options.force_tolerance_ry_per_bohr:.10e}",
                ),
                effect="unit-conversion",
                qualification="QE ionic stopping controls preserve declared units.",
            ),
            *(
                ()
                if lattice_vector_options is None
                else (
                    CalculatorInputMapping(
                        neutral_field="pressure_control",
                        neutral_value=json.dumps(
                            {
                                "pressure_tolerance_kbar": (
                                    convergence.pressure_tolerance_kbar
                                ),
                                "target_pressure_kbar": (
                                    convergence.target_pressure_kbar
                                ),
                            },
                            separators=(",", ":"),
                            sort_keys=True,
                        ),
                        native_fields=("CELL.press", "CELL.press_conv_thr"),
                        native_values=(
                            f"{lattice_vector_options.target_pressure_kbar:.10f}",
                            f"{lattice_vector_options.pressure_tolerance_kbar:.10f}",
                        ),
                        effect="encoding",
                        qualification=(
                            "QE pressure controls use the declared kbar values."
                        ),
                    ),
                )
            ),
            CalculatorInputMapping(
                neutral_field="charge_and_spin",
                neutral_value=json.dumps(
                    {
                        "charge_state": simulation.charge.charge_state,
                        "constrain_spin_channel_difference": (
                            simulation.spin.constrain_spin_channel_difference
                        ),
                        "mode": simulation.spin.mode.value,
                        "spin_channel_electron_difference": (
                            simulation.spin.spin_channel_electron_difference
                        ),
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                native_fields=(
                    "SYSTEM.tot_charge",
                    "SYSTEM.nspin",
                    "SYSTEM.tot_magnetization",
                ),
                native_values=(
                    (
                        str(simulation.charge.charge_state)
                        if simulation.charge.charge_state != 0
                        else "0-default"
                    ),
                    (
                        "2"
                        if simulation.spin.mode is DftSpinMode.COLLINEAR
                        else "1-default"
                    ),
                    (
                        str(simulation.spin.spin_channel_electron_difference)
                        if simulation.spin.constrain_spin_channel_difference
                        else "unconstrained-default"
                    ),
                ),
                effect="encoding",
                qualification=(
                    "Initial spin and constrained final spin remain distinct."
                ),
            ),
            CalculatorInputMapping(
                neutral_field="pseudopotentials",
                neutral_value=json.dumps(
                    [item.sha256 for item in simulation.pseudopotentials],
                    separators=(",", ":"),
                ),
                native_fields=("ATOMIC_SPECIES",),
                native_values=(
                    ",".join(item.filename for item in simulation.pseudopotentials)
                    or "configuration-only-unbound",
                ),
                effect="external-dependency",
                qualification="PseudopotentialLibrary resolves exact bound bytes.",
            ),
        ),
        preparation_operation="projectkoios.qe.pw.relaxation.prepare",
        preparation_version="1",
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
            "tstress = .true.",
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
    use_spatial_symmetry: bool,
    use_time_reversal: bool,
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
    symmetry_lines: tuple[str, ...] = ()
    if not use_spatial_symmetry:
        symmetry_lines += ("nosym = .true.",)
    if not use_time_reversal:
        symmetry_lines += ("noinv = .true.",)
    return QeSystemCard(
        lines=(
            "ibrav = 0",
            f"nat = {atom_count}",
            f"ntyp = {species_count}",
            f"ecutwfc = {wavefunction_cutoff_ry:.10f}",
            f"ecutrho = {wavefunction_cutoff_ry * charge_density_cutoff_ratio:.10f}",
            "occupations = 'fixed'",
            *symmetry_lines,
            *electronic_lines,
        )
    )


def _build_relaxation_electrons_card(
    tolerance_ry: float,
    maximum_iterations: int,
) -> QeElectronsCard:
    return QeElectronsCard(
        lines=(
            f"conv_thr = {tolerance_ry:.10e}",
            f"electron_maxstep = {maximum_iterations}",
        )
    )


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
                    *request.specification.kpoint_sampling.mesh,
                    *request.specification.kpoint_sampling.shift,
                )
            ),
        ),
    )


def _build_relaxation_cell_parameters_card(
    simulation: ResolvedPwDftSimulation,
    *,
    precision: int,
) -> QeCellParametersCard:
    unit_cell = simulation.unit_cell
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
    simulation: ResolvedPwDftSimulation,
    *,
    precision: int,
) -> QeAtomicPositionsCard:
    return QeAtomicPositionsCard(
        option="(crystal)",
        lines=tuple(
            f"{atom.symbol} "
            f"{_format_vector(atom.position_fractional.magnitude, precision)}"
            for atom in simulation.unit_cell.atomic_basis.atoms
        ),
    )


def _conversion_factor(source: str, target: str) -> float:
    return MODEL_SYSTEM_UNIT_CONVERTER.conversion_factor(
        PhysicalUnit(source), PhysicalUnit(target)
    )


def _format_vector(values: NDArray[np.float64], precision: int) -> str:
    first, second, third = values
    return " ".join(f"{float(value):.{precision}f}" for value in (first, second, third))
