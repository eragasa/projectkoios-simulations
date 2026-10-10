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
from projectkoios.integrations.quantumespresso.pw.nscf.cards import (
    QeNscfControlBlock,
    QeNscfOccupations,
    _build_nscf_atomic_species_card,
    _build_nscf_electrons_card,
    _build_nscf_kpoints_card,
    _build_nscf_system_card,
)
from projectkoios.integrations.quantumespresso.pw.nscf.configuration import (  # noqa: E501
    QeNscfProjectionConfiguration,
)
from projectkoios.simulations.dft.pw.settings import CalculationType
from projectkoios.simulations.structure import StructureResolution


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

    control_block: QeNscfControlBlock
    system_card: QeSystemCard
    electrons_card: QeElectronsCard
    atomic_species_card: QeAtomicSpeciesCard
    kpoints_card: QeKpointsCard
    rendered_input: QeNscfRenderedInput
    required_pseudopotential_filenames: tuple[str, ...]
    parent_saved_state_manifest_sha256: str
    band_count: int
    kpoint_count: int
    qualification: str

    def __post_init__(self) -> None:
        for label, value, expected_type in (
            ("control_block", self.control_block, QeNscfControlBlock),
            ("system_card", self.system_card, QeSystemCard),
            ("electrons_card", self.electrons_card, QeElectronsCard),
            ("atomic_species_card", self.atomic_species_card, QeAtomicSpeciesCard),
            ("kpoints_card", self.kpoints_card, QeKpointsCard),
            ("rendered_input", self.rendered_input, QeNscfRenderedInput),
        ):
            if type(value) is not expected_type:
                raise TypeError(f"{label} must be a {expected_type.__name__}")
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

    def project(self, structure: StructureResolution) -> QeNscfInputProjection:
        """Return deterministic input with source-ordered explicit k-points."""
        if type(structure) is not StructureResolution:
            raise TypeError("structure must be a StructureResolution")
        config = self.configuration
        if config.occupations is not QeNscfOccupations.fixed:
            raise NotImplementedError(
                f"NSCF occupations={config.occupations.value!r} is not implemented"
            )
        atoms = structure.unit_cell.atomic_basis.atoms
        if {atom.symbol for atom in atoms} != {item.symbol for item in config.species}:
            raise ValueError("QE species must exactly match the unit cell")
        control_block = QeNscfControlBlock(
            calculation_type=CalculationType.nscf,
            prefix=config.prefix,
            pseudo_dir=config.pseudo_dir,
            outdir=config.outdir,
            verbosity=config.verbosity,
            iprint=config.iprint,
        )
        system_card = _build_nscf_system_card(
            atom_count=len(atoms),
            species_count=len(config.species),
            band_count=config.band_count,
            wavefunction_cutoff_ry=config.wavefunction_cutoff_ry,
            charge_density_cutoff_ry=config.charge_density_cutoff_ry,
            occupations=config.occupations,
            disable_symmetry=config.disable_symmetry,
            disable_time_reversal=config.disable_time_reversal,
        )
        electrons_card = _build_nscf_electrons_card(
            tolerance_ry=config.electronic_tolerance_ry,
            diagonalization=config.diagonalization,
            full_diagonalization_accuracy=config.full_diagonalization_accuracy,
        )
        atomic_species_card = _build_nscf_atomic_species_card(config.species)
        kpoints_card = _build_nscf_kpoints_card(
            tuple((item.coordinates, item.weight) for item in config.kpoints),
            precision=config.kpoint_precision,
        )
        input_file = QePwInputFileAssembler().assemble(
            unit_cell=structure.unit_cell,
            calculation_type=CalculationType.nscf,
            groups=tuple(
                component.to_input_group()
                for component in (
                    system_card,
                    electrons_card,
                    atomic_species_card,
                    kpoints_card,
                )
            ),
            prefix=config.prefix,
            pseudo_dir=config.pseudo_dir,
            outdir=config.outdir,
            cell_parameters_unit="angstrom",
            atomic_positions_unit="crystal",
            coordinate_precision=config.coordinate_precision,
            control_block=control_block,
            card_order=(
                "ATOMIC_SPECIES",
                "CELL_PARAMETERS",
                "ATOMIC_POSITIONS",
                "K_POINTS",
            ),
        )
        return QeNscfInputProjection(
            control_block=control_block,
            system_card=system_card,
            electrons_card=electrons_card,
            atomic_species_card=atomic_species_card,
            kpoints_card=kpoints_card,
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
