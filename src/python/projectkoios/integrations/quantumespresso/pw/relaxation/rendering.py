"""Render validated Quantum ESPRESSO relaxation calculations."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.integrations.quantumespresso.pw.inputfile.base import QeAtomicSpecies
from projectkoios.integrations.quantumespresso.pw.inputfile.cell import (
    QeCellDegreesOfFreedom,
)
from projectkoios.integrations.quantumespresso.pw.relax.configuration import (  # noqa: E501
    QeRelaxProjectionConfiguration,
)
from projectkoios.integrations.quantumespresso.pw.relax.projection import (  # noqa: E501
    QeRelaxInputProjector,
)
from projectkoios.integrations.quantumespresso.pw.vc_relax.configuration import (  # noqa: E501
    QeVcRelaxProjectionConfiguration,
)
from projectkoios.integrations.quantumespresso.pw.vc_relax.projection import (  # noqa: E501
    QeVcRelaxInputProjector,
)
from projectkoios.physkit.units import MODEL_SYSTEM_UNIT_CONVERTER, PhysicalUnit
from projectkoios.simulations.dft.electronic import (
    DftExchangeCorrelationIdentifierScheme,
    DftExchangeCorrelationModel,
    DftOccupationMethod,
    DftOccupationPolicy,
    PwDftElectronicConvergencePolicy,
)
from projectkoios.simulations.dft.pseudopotential import (
    Pseudopotential,
    PseudopotentialArtifactFormat,
    PseudopotentialFile,
)
from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftCellRelaxationMode,
    PwDftRelaxationConvergencePolicy,
    PwDftRelaxationDegreesOfFreedom,
    PwDftRelaxationInitialization,
)
from projectkoios.simulations.dft.pw.relaxation.request import PwDftRelaxationRequest
from projectkoios.simulations.dft.pw.relaxation.specification import (
    PwDftRelaxationSpecification,
)
from projectkoios.simulations.dft.pw.settings import PwDftKPointSamplingPolicy
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation
from projectkoios.simulations.structure import StructureResolution

from .calculation import QeRelaxationCalculationConfiguration


@dataclass(frozen=True, slots=True)
class QeRelaxationCalculationRenderer:
    """Project a calculation configuration and exact structure into QE input."""

    def render(
        self,
        configuration: QeRelaxationCalculationConfiguration,
        structure: StructureResolution,
    ) -> str:
        """Return one phase-specific Quantum ESPRESSO input document."""
        if type(configuration) is not QeRelaxationCalculationConfiguration:
            raise TypeError(
                "configuration must be a QeRelaxationCalculationConfiguration"
            )
        if type(structure) is not StructureResolution:
            raise TypeError("structure must be a StructureResolution")
        if structure.record.structure_id != configuration.structure.structure_id:
            raise ValueError("resolved structure identity must match configuration")
        if (
            structure.record.sha256 != configuration.structure.sha256
            or structure.record.byte_size != configuration.structure.byte_size
        ):
            raise ValueError("resolved structure bytes must match configuration")

        phase = configuration.phase
        ionic_options = configuration.ionic_relaxation
        lattice_options = configuration.lattice_vector_relaxation
        if configuration.pseudopotential_exchange_correlation != "PBE":
            raise NotImplementedError(
                "only the reviewed PBE-to-Libxc QE relaxation mapping is implemented"
            )

        # The provider configuration predates SimulationLibrary. This explicit
        # mapping preserves its reviewed PBE meaning without guessing for any
        # other label; unsupported labels fail before native input is rendered.
        exchange_correlation = DftExchangeCorrelationModel(
            identifier_scheme=(DftExchangeCorrelationIdentifierScheme.LIBXC_COMPOSITE),
            identifier="GGA_X_PBE+GGA_C_PBE",
            pseudopotential_compatibility_label="PBE",
        )
        cell_mode = PwDftCellRelaxationMode.FIXED
        if lattice_options is not None:
            cell_mode = {
                QeCellDegreesOfFreedom.ALL: (
                    PwDftCellRelaxationMode.UNRESTRICTED_VECTORS
                ),
                QeCellDegreesOfFreedom.VOLUME: PwDftCellRelaxationMode.VOLUME_ONLY,
                QeCellDegreesOfFreedom.SHAPE: (
                    PwDftCellRelaxationMode.SHAPE_AT_FIXED_VOLUME
                ),
            }.get(lattice_options.degrees_of_freedom)  # type: ignore[assignment]
            if cell_mode is None:
                raise NotImplementedError(
                    "configured QE cell degrees of freedom have no exact "
                    "neutral mapping"
                )
        request = PwDftRelaxationRequest(
            evaluation_id=f"{configuration.calculation_id}-{phase}",
            specification=PwDftRelaxationSpecification(
                simulation_id=(
                    f"{structure.record.structure_id}.QE."
                    f"{'VcRelax' if phase == 'vc-relax' else 'Relax'}"
                ),
                simulation=PwDftSimulation(
                    structure=structure.record,
                    exchange_correlation=exchange_correlation,
                    pseudopotentials=(
                        PseudopotentialFile(
                            pseudopotential=Pseudopotential(
                                symbol=configuration.pseudopotential_symbol,
                                exchange_correlation=(
                                    configuration.pseudopotential_exchange_correlation
                                ),
                                formalism=configuration.pseudopotential_formalism,
                                relativistic_treatment=(
                                    configuration.pseudopotential_relativistic_treatment
                                ),
                                valence_electrons=(
                                    configuration.pseudopotential_valence_electrons
                                ),
                            ),
                            artifact_format=PseudopotentialArtifactFormat.UPF,
                            artifact_format_version=(
                                configuration.pseudopotential_upf_version
                            ),
                            filename=configuration.pseudopotential_filename,
                            sha256=configuration.pseudopotential.sha256,
                            byte_size=configuration.pseudopotential.byte_size,
                        ),
                    ),
                ),
                kpoint_sampling=PwDftKPointSamplingPolicy(
                    mesh=configuration.kpoint_mesh,
                    shift=configuration.kpoint_shift,
                    use_spatial_symmetry=True,
                    use_time_reversal=True,
                ),
                wavefunction_cutoff_ev=_convert(
                    configuration.wavefunction_cutoff_ry,
                    "Ry",
                    "eV",
                ),
                occupation=DftOccupationPolicy(method=DftOccupationMethod.FIXED),
                electronic_convergence=PwDftElectronicConvergencePolicy(
                    energy_tolerance_ev=_convert(
                        configuration.electronic_tolerance_ry,
                        "Ry",
                        "eV",
                    ),
                    maximum_electronic_iterations=100,
                ),
                initialization=(
                    PwDftRelaxationInitialization.FROM_EXACT_STARTING_STRUCTURE
                ),
                degrees_of_freedom=PwDftRelaxationDegreesOfFreedom(
                    relax_atomic_positions=True,
                    cell_mode=cell_mode,
                ),
                ionic_convergence=PwDftRelaxationConvergencePolicy(
                    maximum_ionic_steps=ionic_options.maximum_steps,
                    total_energy_tolerance_ev=_convert(
                        ionic_options.total_energy_tolerance_ry,
                        "Ry",
                        "eV",
                    ),
                    force_tolerance_ev_per_angstrom=_convert(
                        ionic_options.force_tolerance_ry_per_bohr,
                        "Ry/bohr",
                        "eV/angstrom",
                    ),
                    target_pressure_kbar=(
                        None
                        if lattice_options is None
                        else lattice_options.target_pressure_kbar
                    ),
                    pressure_tolerance_kbar=(
                        None
                        if lattice_options is None
                        else lattice_options.pressure_tolerance_kbar
                    ),
                ),
            ),
        )
        species = (
            QeAtomicSpecies(
                symbol=configuration.pseudopotential_symbol,
                mass_amu=configuration.pseudopotential_mass_amu,
                pseudopotential_filename=configuration.pseudopotential_filename,
            ),
        )
        ratio = (
            configuration.charge_density_cutoff_ry
            / configuration.wavefunction_cutoff_ry
        )
        if phase == "relax":
            projection = QeRelaxInputProjector(
                QeRelaxProjectionConfiguration(
                    species=species,
                    ion_dynamics=ionic_options.dynamics,
                    charge_density_cutoff_ratio=ratio,
                    electronic_tolerance_ry=configuration.electronic_tolerance_ry,
                    electronic_atol_ry=configuration.electronic_atol_ry,
                    prefix=configuration.prefix,
                    pseudo_dir=configuration.pseudo_dir,
                    outdir=configuration.outdir,
                    input_filename=configuration.input_filename,
                    coordinate_precision=configuration.coordinate_precision,
                )
            ).project(request, structure)
        else:
            assert lattice_options is not None
            projection = QeVcRelaxInputProjector(
                QeVcRelaxProjectionConfiguration(
                    species=species,
                    ion_dynamics=ionic_options.dynamics,
                    charge_density_cutoff_ratio=ratio,
                    electronic_tolerance_ry=configuration.electronic_tolerance_ry,
                    electronic_atol_ry=configuration.electronic_atol_ry,
                    prefix=configuration.prefix,
                    pseudo_dir=configuration.pseudo_dir,
                    outdir=configuration.outdir,
                    input_filename=configuration.input_filename,
                    coordinate_precision=configuration.coordinate_precision,
                    cell_dynamics=lattice_options.dynamics,
                    cell_degrees_of_freedom=lattice_options.degrees_of_freedom,
                )
            ).project(request, structure)
        primary = tuple(
            artifact
            for artifact in projection.artifacts
            if artifact.role == "primary-input"
        )
        if len(primary) != 1:
            raise ValueError("QE relaxation input must contain one primary artifact")
        return primary[0].content.decode("ascii")


def _convert(value: float, source: str, target: str) -> float:
    return value * MODEL_SYSTEM_UNIT_CONVERTER.conversion_factor(
        PhysicalUnit(source),
        PhysicalUnit(target),
    )
