"""Project explicit Wannier-oriented NSCF declarations into ``pw.x`` input."""

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
from projectkoios.integrations.quantumespresso.pw.nscf.configuration import (  # noqa: E501
    QeNscfOccupations,
    QeNscfProjectionConfiguration,
)
from projectkoios.simulations.dft.pw.settings import CalculationType
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation


@dataclass(frozen=True, slots=True)
class QeNscfRenderedInput:
    """Represent one deterministic native NSCF input file."""

    filename: str
    text: str

    def __post_init__(self) -> None:
        if (
            type(self.filename) is not str
            or not self.filename
            or self.filename in {".", ".."}
            or "/" in self.filename
            or "\\" in self.filename
        ):
            raise ValueError("filename must be a basename")
        if type(self.text) is not str:
            raise TypeError("text must be a string")


@dataclass(frozen=True, slots=True)
class QeNscfInputProjection:
    """Retain rendered NSCF input and its unresolved native dependencies."""

    rendered_input: QeNscfRenderedInput
    required_pseudopotential_filenames: tuple[str, ...]
    parent_saved_state_manifest_sha256: str
    band_count: int
    kpoint_count: int
    qualification: str

    def __post_init__(self) -> None:
        if type(self.rendered_input) is not QeNscfRenderedInput:
            raise TypeError("rendered_input must be a QeNscfRenderedInput")
        if (
            type(self.required_pseudopotential_filenames) is not tuple
            or not self.required_pseudopotential_filenames
        ):
            raise ValueError("required pseudopotential filenames must be nonempty")
        if len(set(self.required_pseudopotential_filenames)) != len(
            self.required_pseudopotential_filenames
        ):
            raise ValueError("required pseudopotential filenames must be unique")
        if type(self.band_count) is not int or self.band_count <= 0:
            raise ValueError("band_count must be positive")
        if type(self.kpoint_count) is not int or self.kpoint_count <= 0:
            raise ValueError("kpoint_count must be positive")
        if type(self.qualification) is not str or not self.qualification:
            raise ValueError("qualification must be nonempty")


@dataclass(frozen=True, slots=True)
class QeNscfInputProjector:
    """Render one explicit QE NSCF calculation without executing ``pw.x``."""

    configuration: QeNscfProjectionConfiguration

    def __post_init__(self) -> None:
        if type(self.configuration) is not QeNscfProjectionConfiguration:
            raise TypeError("configuration must be a QeNscfProjectionConfiguration")

    def project(self, simulation: PwDftSimulation) -> QeNscfInputProjection:
        """Return deterministic input with source-ordered explicit k-points."""
        if type(simulation) is not PwDftSimulation:
            raise TypeError("simulation must be a PwDftSimulation")
        if simulation.settings.calculation_type is not CalculationType.nscf:
            raise ValueError("simulation calculation type must be nscf")
        config = self.configuration
        if config.occupations is not QeNscfOccupations.fixed:
            raise NotImplementedError(
                f"NSCF occupations={config.occupations.value!r} is not implemented"
            )
        atoms = simulation.unit_cell.atomic_basis.atoms
        if {atom.symbol for atom in atoms} != {item.symbol for item in config.species}:
            raise ValueError("QE species must exactly match the unit cell")
        input_file = QePwInputFileAssembler().assemble(
            simulation=simulation,
            groups=tuple(
                component.to_input_group()
                for component in (
                    QeSystemCard(
                        lines=(
                            "ibrav = 0",
                            f"nat = {len(atoms)}",
                            f"ntyp = {len(config.species)}",
                            f"nbnd = {config.band_count}",
                            f"ecutwfc = {config.wavefunction_cutoff_ry:.10f}",
                            f"ecutrho = {config.charge_density_cutoff_ry:.10f}",
                            f"occupations = '{config.occupations.value}'",
                            "nosym = .true.",
                            "noinv = .true.",
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
                        option="crystal",
                        lines=(
                            str(len(config.kpoints)),
                            *tuple(
                                self._render_kpoint(item.coordinates, item.weight)
                                for item in config.kpoints
                            ),
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
        return QeNscfInputProjection(
            rendered_input=QeNscfRenderedInput(
                filename=config.input_filename,
                text=PwInputWriter().render(input_file),
            ),
            required_pseudopotential_filenames=tuple(
                item.pseudopotential_filename for item in config.species
            ),
            parent_saved_state_manifest_sha256=(
                config.parent_saved_state_manifest_sha256
            ),
            band_count=config.band_count,
            kpoint_count=len(config.kpoints),
            qualification=(
                "QE NSCF projection with explicit source-ordered crystal k-points, "
                "fixed occupations, disabled symmetry and inversion reduction, and "
                "an identity-bound parent saved-state manifest."
            ),
        )

    def _render_kpoint(
        self,
        coordinates: tuple[float, float, float],
        weight: float,
    ) -> str:
        precision = self.configuration.kpoint_precision
        return " ".join(f"{value:.{precision}f}" for value in (*coordinates, weight))
