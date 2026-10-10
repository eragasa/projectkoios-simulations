"""Project calculator-neutral SCF requests into Quantum ESPRESSO input."""

from __future__ import annotations

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
from projectkoios.simulations.dft.electronic import DftSpinMode
from projectkoios.simulations.dft.pseudopotential import (
    PseudopotentialArtifactFormat,
)
from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfRequest,
)
from projectkoios.simulations.dft.pw.scf.integration import (
    PwDftScfInputProjection,
    PwDftScfRenderedInput,
)

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

    def project(self, request: PwDftScfRequest) -> PwDftScfInputProjection:
        """Return deterministic ``pw.in`` text and pseudopotential requirements."""
        if type(request) is not PwDftScfRequest:
            raise TypeError("request must be a PwDftScfRequest")
        config = self.configuration
        atoms = request.simulation.unit_cell.atomic_basis.atoms
        atom_symbols = {atom.symbol for atom in atoms}
        configured_symbols = {item.symbol for item in config.species}
        if atom_symbols != configured_symbols:
            raise ValueError(
                "QE species configuration must exactly match the unit cell"
            )
        if request.simulation.pseudopotentials:
            if any(
                item.artifact_format is not PseudopotentialArtifactFormat.UPF
                for item in request.simulation.pseudopotentials
            ):
                raise ValueError("QE translation requires UPF pseudopotentials")
            configured_filenames = {
                item.symbol: item.pseudopotential_filename for item in config.species
            }
            bound_filenames = {
                item.symbol: item.filename
                for item in request.simulation.pseudopotentials
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
                "QE SCF translation supports only unpolarized and collinear spin"
            )
        if request.simulation.spin.initial_site_magnetic_moments_mu_b:
            raise NotImplementedError(
                "QE SCF translation of site-resolved initial moments is not implemented"
            )
        electronic_lines: tuple[str, ...] = ()
        if request.simulation.charge.charge_state != 0:
            electronic_lines += (
                f"tot_charge = {request.simulation.charge.charge_state},",
            )
        if request.simulation.spin.mode is DftSpinMode.COLLINEAR:
            electronic_lines += ("nspin = 2,",)
            if request.simulation.spin.constrain_spin_channel_difference:
                electronic_lines += (
                    "tot_magnetization = "
                    f"{request.simulation.spin.spin_channel_electron_difference},",
                )

        cutoff_ry = self._ev_to_ry(request.sampling.wavefunction_cutoff_ev)
        charge_density_cutoff_ry = cutoff_ry * config.charge_density_cutoff_ratio
        mesh = request.sampling.kpoint_mesh
        shift = request.sampling.kpoint_shift
        input_file = QePwInputFileAssembler().assemble(
            simulation=request.simulation,
            groups=tuple(
                component.to_input_group()
                for component in (
                    QeSystemCard(
                        lines=(
                            "ibrav = 0,",
                            f"nat = {len(atoms)},",
                            f"ntyp = {len(config.species)},",
                            f"ecutwfc = {cutoff_ry:.10f},",
                            f"ecutrho = {charge_density_cutoff_ry:.10f}",
                            *electronic_lines,
                        )
                    ),
                    QeElectronsCard(
                        lines=(f"conv_thr = {config.electronic_tolerance_ry:.10e}",)
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
        return PwDftScfInputProjection(
            integration_id=QE_SCF_INTEGRATION_ID,
            rendered_inputs=(
                PwDftScfRenderedInput(
                    filename=config.input_filename,
                    text=PwInputWriter().render(input_file),
                ),
            ),
            required_external_inputs=tuple(
                item.pseudopotential_filename for item in config.species
            ),
            qualification=(
                "QE ibrav=0 projection with explicit angstrom cell vectors, crystal "
                "positions, automatic k-point sampling, and calculator-native SCF "
                "policy."
            ),
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
