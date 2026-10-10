"""Project calculator-neutral SCF requests into Quantum ESPRESSO input."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeAtomicSpeciesCard,
    QeElectronsCard,
    QeKpointsCard,
    QePwInputFileAssembler,
    QeSystemCard,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.model import (
    PwInputWriter,
)
from projectkoios.integrations.quantumespresso.pw.scf import (
    configuration as qe_configuration,
)
from projectkoios.physkit.units import (
    MODEL_SYSTEM_UNIT_CONVERTER,
    PhysicalUnit,
    ScalarQuantity,
)
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
from projectkoios.simulations.dft.pw.scf.request import PwDftScfRequest
from projectkoios.simulations.dft.pw.settings import CalculationType
from projectkoios.simulations.dft.pw.simulation import ResolvedPwDftSimulation
from projectkoios.simulations.library.codec import simulation_source_reference
from projectkoios.simulations.structure import StructureResolution

QE_SCF_INTEGRATION_ID = CalculatorIntegrationId(value="quantum-espresso")


@dataclass(frozen=True, slots=True)
class QeScfInputProjector:
    """Render one common SCF request using explicit QE-native policy."""

    configuration: qe_configuration.QeScfProjectionConfiguration

    def __post_init__(self) -> None:
        if (
            type(self.configuration)
            is not qe_configuration.QeScfProjectionConfiguration
        ):
            raise TypeError("configuration must be a QeScfProjectionConfiguration")

    def project(
        self,
        request: PwDftScfRequest,
        structure: StructureResolution,
    ) -> CalculatorInputRecord:
        """Return exact ``pw.in`` bytes and pseudopotential requirements."""
        if type(request) is not PwDftScfRequest:
            raise TypeError("request must be a PwDftScfRequest")
        if type(structure) is not StructureResolution:
            raise TypeError("structure must be a StructureResolution")
        specification = request.specification
        simulation = specification.simulation
        resolved = ResolvedPwDftSimulation(simulation=simulation, structure=structure)
        config = self.configuration
        atoms = resolved.unit_cell.atomic_basis.atoms
        atom_symbols = {atom.symbol for atom in atoms}
        configured_symbols = {item.symbol for item in config.species}
        if atom_symbols != configured_symbols:
            raise ValueError(
                "QE species configuration must exactly match the unit cell"
            )
        if not simulation.pseudopotentials:
            raise ValueError("QE translation requires exact bound pseudopotentials")
        if any(
            item.artifact_format is not PseudopotentialArtifactFormat.UPF
            for item in simulation.pseudopotentials
        ):
            raise ValueError("QE translation requires UPF pseudopotentials")
        configured_filenames = {
            item.symbol: item.pseudopotential_filename for item in config.species
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
                "QE SCF translation supports only unpolarized and collinear spin"
            )
        electronic_lines: tuple[str, ...] = ()
        if simulation.charge.charge_state != 0:
            electronic_lines += (f"tot_charge = {simulation.charge.charge_state},",)
        if simulation.spin.mode is DftSpinMode.COLLINEAR:
            electronic_lines += ("nspin = 2,",)
            if simulation.spin.constrain_spin_channel_difference:
                electronic_lines += (
                    "tot_magnetization = "
                    f"{simulation.spin.spin_channel_electron_difference},",
                )
        if simulation.spin.initial_site_magnetic_moments_mu_b:
            if not simulation.pseudopotentials:
                raise ValueError(
                    "QE initial magnetization requires exact pseudopotential "
                    "valence-electron identities"
                )
            pseudopotential_by_symbol = {
                item.symbol: item.pseudopotential
                for item in simulation.pseudopotentials
            }
            moments = simulation.spin.initial_site_magnetic_moments_mu_b
            for species_index, species in enumerate(config.species, start=1):
                species_moments = tuple(
                    moment
                    for atom, moment in zip(atoms, moments, strict=True)
                    if atom.symbol == species.symbol
                )
                reference_moment = species_moments[0]
                if any(
                    not math.isclose(
                        value,
                        reference_moment,
                        rel_tol=0.0,
                        abs_tol=config.magnetic_moment_atol_mu_b,
                    )
                    for value in species_moments[1:]
                ):
                    raise NotImplementedError(
                        "QE species-level starting magnetization cannot represent "
                        "different site moments for one species"
                    )
                valence_electrons = pseudopotential_by_symbol[
                    species.symbol
                ].valence_electrons
                starting_magnetization = reference_moment / valence_electrons
                if abs(starting_magnetization) > 1.0:
                    raise ValueError(
                        "QE starting magnetization fraction must be between -1 and 1"
                    )
                electronic_lines += (
                    f"starting_magnetization({species_index}) = "
                    f"{starting_magnetization:.10f},",
                )

        occupation_lines: tuple[str, ...] = ()
        if specification.occupation.method is DftOccupationMethod.FIXED:
            pass
        elif specification.occupation.method is DftOccupationMethod.GAUSSIAN:
            assert specification.occupation.smearing_width_ev is not None
            occupation_lines = (
                "occupations = 'smearing',",
                "smearing = 'gaussian',",
                "degauss = "
                f"{self._ev_to_ry(specification.occupation.smearing_width_ev):.10e},",
            )
        else:
            raise NotImplementedError(
                "QE SCF translation supports fixed or Gaussian occupations"
            )

        symmetry_lines: tuple[str, ...] = ()
        if not specification.kpoint_sampling.use_spatial_symmetry:
            symmetry_lines += ("nosym = .true.,",)
        if not specification.kpoint_sampling.use_time_reversal:
            symmetry_lines += ("noinv = .true.,",)
        neutral_tolerance_ry = self._ev_to_ry(
            specification.electronic_convergence.energy_tolerance_ev
        )
        if not math.isclose(
            neutral_tolerance_ry,
            config.electronic_tolerance_ry,
            rel_tol=0.0,
            abs_tol=config.electronic_atol_ry,
        ):
            raise ValueError(
                "QE configuration electronic tolerance must match specification"
            )

        cutoff_ry = self._ev_to_ry(specification.wavefunction_cutoff_ev)
        charge_density_cutoff_ry = cutoff_ry * config.charge_density_cutoff_ratio
        mesh = specification.kpoint_sampling.mesh
        shift = specification.kpoint_sampling.shift
        input_file = QePwInputFileAssembler().assemble(
            unit_cell=resolved.unit_cell,
            calculation_type=CalculationType.scf,
            groups=tuple(
                component.to_input_group()
                for component in (
                    QeSystemCard(
                        lines=(
                            "ibrav = 0,",
                            f"nat = {len(atoms)},",
                            f"ntyp = {len(config.species)},",
                            f"ecutwfc = {cutoff_ry:.10f},",
                            f"ecutrho = {charge_density_cutoff_ry:.10f},",
                            *symmetry_lines,
                            *occupation_lines,
                            *electronic_lines,
                        )
                    ),
                    QeElectronsCard(
                        lines=(
                            f"conv_thr = {config.electronic_tolerance_ry:.10e},",
                            "electron_maxstep = "
                            f"{specification.electronic_convergence.maximum_electronic_iterations}",
                        )
                    ),
                    QeAtomicSpeciesCard(
                        lines=tuple(
                            f"{item.symbol} {item.mass_amu:.10g} "
                            f"{item.pseudopotential_filename}"
                            for item in config.species
                        )
                    ),
                    QeKpointsCard(
                        option="automatic",
                        lines=(
                            f"{mesh[0]} {mesh[1]} {mesh[2]} "
                            f"{shift[0]} {shift[1]} {shift[2]}",
                        ),
                    ),
                )
            ),
            prefix=config.prefix,
            pseudo_dir=config.pseudo_dir,
            outdir=config.outdir,
            cell_parameters_unit="angstrom",
            atomic_positions_unit="crystal",
            coordinate_precision=config.coordinate_precision,
            card_order=(
                "ATOMIC_SPECIES",
                "CELL_PARAMETERS",
                "ATOMIC_POSITIONS",
                "K_POINTS",
            ),
        )
        rendered_content = PwInputWriter().render(input_file).encode("ascii")
        source = simulation_source_reference(specification)
        spin_native_fields = ["SYSTEM.nspin"]
        spin_native_values = [
            "2" if simulation.spin.mode is DftSpinMode.COLLINEAR else "1-default"
        ]
        if simulation.spin.constrain_spin_channel_difference:
            spin_native_fields.append("SYSTEM.tot_magnetization")
            spin_native_values.append(
                str(simulation.spin.spin_channel_electron_difference)
            )
        if simulation.spin.initial_site_magnetic_moments_mu_b:
            for species_index, species in enumerate(config.species, start=1):
                spin_native_fields.append(
                    f"SYSTEM.starting_magnetization({species_index})"
                )
                species_moment = next(
                    moment
                    for atom, moment in zip(atoms, moments, strict=True)
                    if atom.symbol == species.symbol
                )
                valence_electrons = pseudopotential_by_symbol[
                    species.symbol
                ].valence_electrons
                spin_native_values.append(f"{species_moment / valence_electrons:.10f}")
        occupation_native_fields: tuple[str, ...] = ("SYSTEM.occupations",)
        smearing_width_ry = self._ev_to_ry(
            specification.occupation.smearing_width_ev or 0.0
        )
        occupation_native_values: tuple[str, ...] = (
            ("fixed-default",)
            if specification.occupation.method is DftOccupationMethod.FIXED
            else (
                "smearing",
                "gaussian",
                f"{smearing_width_ry:.10e}",
            )
        )
        if specification.occupation.method is DftOccupationMethod.GAUSSIAN:
            occupation_native_fields = (
                "SYSTEM.occupations",
                "SYSTEM.smearing",
                "SYSTEM.degauss",
            )

        electronic_convergence = specification.electronic_convergence
        spin = simulation.spin

        # The prepared record binds rendered bytes to canonical specification
        # identity. Evaluation IDs are deliberately absent so a retry cannot
        # manufacture a different scientific input identity.
        return CalculatorInputRecord(
            input_id=f"{specification.simulation_id}.QuantumEspresso.PreparedInput",
            schema_version=1,
            source=source,
            integration_id=QE_SCF_INTEGRATION_ID,
            calculator_name="Quantum ESPRESSO pw.x",
            calculator_version_constraint=">=7.5,<8",
            representation="quantum-espresso-pw-input",
            artifacts=(
                CalculatorInputArtifact(
                    role="primary-input",
                    filename=config.input_filename,
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
                        f"{simulation.structure.structure_id}/"
                        f"{simulation.structure.sha256}"
                    ),
                    native_fields=(
                        "CELL_PARAMETERS",
                        "ATOMIC_POSITIONS",
                    ),
                    native_values=("angstrom", "crystal"),
                    effect="encoding",
                    qualification="Exact verified structure geometry is rendered.",
                ),
                CalculatorInputMapping(
                    neutral_field="wavefunction_cutoff_ev",
                    neutral_value=f"{specification.wavefunction_cutoff_ev:.17g}",
                    native_fields=("SYSTEM.ecutwfc", "SYSTEM.ecutrho"),
                    native_values=(
                        f"{cutoff_ry:.10f}",
                        f"{charge_density_cutoff_ry:.10f}",
                    ),
                    effect="unit-conversion",
                    qualification="The configured density-cutoff ratio is explicit.",
                ),
                CalculatorInputMapping(
                    neutral_field="occupation",
                    neutral_value=json.dumps(
                        {
                            "method": specification.occupation.method.value,
                            "smearing_width_ev": (
                                specification.occupation.smearing_width_ev
                            ),
                        },
                        allow_nan=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                    native_fields=occupation_native_fields,
                    native_values=occupation_native_values,
                    effect="encoding",
                    qualification="Unsupported occupation families fail closed.",
                ),
                CalculatorInputMapping(
                    neutral_field="electronic_convergence",
                    neutral_value=json.dumps(
                        {
                            "energy_tolerance_ev": (
                                electronic_convergence.energy_tolerance_ev
                            ),
                            "maximum_electronic_iterations": (
                                electronic_convergence.maximum_electronic_iterations
                            ),
                        },
                        allow_nan=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                    native_fields=("ELECTRONS.conv_thr", "ELECTRONS.electron_maxstep"),
                    native_values=(
                        f"{config.electronic_tolerance_ry:.10e}",
                        str(
                            specification.electronic_convergence.maximum_electronic_iterations
                        ),
                    ),
                    effect="unit-conversion",
                    qualification="The eV-to-Ry mapping passed configured tolerance.",
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
                        f"{mesh[0]} {mesh[1]} {mesh[2]} "
                        f"{shift[0]} {shift[1]} {shift[2]}",
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
                    qualification=(
                        "QE nosym and noinv encode disabled symmetry reductions; "
                        "omitted false values use documented native defaults."
                    ),
                ),
                CalculatorInputMapping(
                    neutral_field="charge",
                    neutral_value=str(simulation.charge.charge_state),
                    native_fields=("SYSTEM.tot_charge",),
                    native_values=(
                        str(simulation.charge.charge_state)
                        if simulation.charge.charge_state != 0
                        else "0-default",
                    ),
                    effect="encoding",
                    qualification="QE positive tot_charge removes electrons.",
                ),
                CalculatorInputMapping(
                    neutral_field="spin",
                    neutral_value=json.dumps(
                        {
                            "constrained_difference": (
                                spin.constrain_spin_channel_difference
                            ),
                            "difference": spin.spin_channel_electron_difference,
                            "initial_site_moments_mu_b": (
                                spin.initial_site_magnetic_moments_mu_b
                            ),
                            "mode": spin.mode.value,
                        },
                        allow_nan=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                    native_fields=tuple(spin_native_fields),
                    native_values=tuple(spin_native_values),
                    effect="encoding",
                    qualification=(
                        "Initial moments and final-spin constraints remain distinct."
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
                        ",".join(item.filename for item in simulation.pseudopotentials),
                    ),
                    effect="external-dependency",
                    qualification="PseudopotentialLibrary must resolve exact bytes.",
                ),
            ),
            preparation_operation="projectkoios.qe.pw.scf.prepare",
            preparation_version="1",
        )

    @staticmethod
    def _ev_to_ry(value: float) -> float:
        converted = MODEL_SYSTEM_UNIT_CONVERTER.convert_scalar(
            ScalarQuantity(
                magnitude=value,
                unit=PhysicalUnit(expression="eV"),
            ),
            PhysicalUnit(expression="Ry"),
        )
        return converted.magnitude
