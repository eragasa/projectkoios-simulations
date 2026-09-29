"""Define one path-complete, provenance-bound QE NSCF calculation."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeAtomicSpecies,
)
from projectkoios.integrations.quantumespresso.pw.nscf.cards import (
    QeNscfDiagonalization,
    QeNscfOccupations,
    QeNscfVerbosity,
)
from projectkoios.integrations.quantumespresso.pw.nscf.configuration import (
    QeNscfKPoint,
    QeNscfProjectionConfiguration,
)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_IDENTIFIER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_ELEMENT = re.compile(r"[A-Z][a-z]?\Z")


@dataclass(frozen=True, slots=True)
class QeNscfFileResource:
    """Identify one configured external file by path and exact byte identity."""

    path: str
    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        _path_text(self.path, "path")
        _sha256(self.sha256, "sha256")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("byte_size must be positive")

    def resolve(self, configuration_directory: Path) -> Path:
        """Resolve relative paths against the owning configuration directory."""
        path = Path(self.path).expanduser()
        return (
            path.absolute()
            if path.is_absolute()
            else (configuration_directory / path).absolute()
        )


@dataclass(frozen=True, slots=True)
class QeNscfDirectoryResource:
    """Declare one configured directory path without asserting its contents."""

    path: str

    def __post_init__(self) -> None:
        _path_text(self.path, "path")

    def resolve(self, configuration_directory: Path) -> Path:
        """Resolve relative paths against the owning configuration directory."""
        path = Path(self.path).expanduser()
        return (
            path.absolute()
            if path.is_absolute()
            else (configuration_directory / path).absolute()
        )


@dataclass(frozen=True, slots=True)
class QeNscfCalculationConfiguration:
    """Hold all projection and runtime resource declarations for one NSCF run."""

    calculation_id: str
    integration_id: str
    source_input: QeNscfFileResource
    structure: QeNscfFileResource
    structure_id: str
    calculator: QeNscfFileResource
    calculator_program: str
    calculator_version: str
    pseudopotential: QeNscfFileResource
    pseudopotential_symbol: str
    pseudopotential_filename: str
    pseudopotential_mass_amu: float
    parent_output_directory: QeNscfDirectoryResource
    parent_saved_state_root: QeNscfDirectoryResource
    parent_manifest: QeNscfFileResource
    parent_calculation: str
    parent_prefix: str
    output_directory: QeNscfDirectoryResource
    reference_output_directory: QeNscfDirectoryResource | None
    kpoint_grid: tuple[int, int, int]
    kpoint_offset: tuple[int, int, int]
    band_count: int
    wavefunction_cutoff_ry: float
    charge_density_cutoff_ry: float | None
    electronic_tolerance_ry: float
    occupations: QeNscfOccupations
    prefix: str
    pseudo_dir: str
    outdir: str
    input_filename: str
    verbosity: QeNscfVerbosity
    iprint: int
    diagonalization: QeNscfDiagonalization
    full_diagonalization_accuracy: bool
    disable_symmetry: bool
    disable_time_reversal: bool
    coordinate_precision: int
    kpoint_precision: int
    qualification_statements: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            type(self.calculation_id) is not str
            or _IDENTIFIER.fullmatch(self.calculation_id) is None
        ):
            raise ValueError("calculation_id must be a lowercase slug")
        if self.integration_id != "quantum-espresso":
            raise ValueError("integration_id must be quantum-espresso")
        for label, resource_value, expected_type in (
            ("source_input", self.source_input, QeNscfFileResource),
            ("structure", self.structure, QeNscfFileResource),
            ("calculator", self.calculator, QeNscfFileResource),
            ("pseudopotential", self.pseudopotential, QeNscfFileResource),
            ("parent_manifest", self.parent_manifest, QeNscfFileResource),
            (
                "parent_output_directory",
                self.parent_output_directory,
                QeNscfDirectoryResource,
            ),
            (
                "parent_saved_state_root",
                self.parent_saved_state_root,
                QeNscfDirectoryResource,
            ),
            ("output_directory", self.output_directory, QeNscfDirectoryResource),
        ):
            if type(resource_value) is not expected_type:
                raise TypeError(f"{label} has the wrong resource type")
        if self.reference_output_directory is not None and (
            type(self.reference_output_directory) is not QeNscfDirectoryResource
        ):
            raise TypeError("reference_output_directory must be a directory or None")
        for label, text_value in (
            ("structure_id", self.structure_id),
            ("calculator_version", self.calculator_version),
        ):
            if (
                type(text_value) is not str
                or not text_value
                or text_value != text_value.strip()
            ):
                raise ValueError(f"{label} must be nonempty and stripped")
        if self.calculator_program != "pw.x":
            raise ValueError("calculator_program must be pw.x")
        if (
            type(self.pseudopotential_symbol) is not str
            or _ELEMENT.fullmatch(self.pseudopotential_symbol) is None
        ):
            raise ValueError("pseudopotential_symbol must be an element symbol")
        _basename(self.pseudopotential_filename, "pseudopotential_filename")
        if self.pseudopotential_filename != Path(self.pseudopotential.path).name:
            raise ValueError(
                "pseudopotential_filename must match the configured resource basename"
            )
        if (
            type(self.pseudopotential_mass_amu) is not float
            or not math.isfinite(self.pseudopotential_mass_amu)
            or self.pseudopotential_mass_amu <= 0.0
        ):
            raise ValueError("pseudopotential_mass_amu must be positive and finite")
        if self.parent_calculation != "scf":
            raise ValueError("parent_calculation must be scf")
        for label, prefix_value in (
            ("parent_prefix", self.parent_prefix),
            ("prefix", self.prefix),
        ):
            if (
                type(prefix_value) is not str
                or _IDENTIFIER.fullmatch(prefix_value) is None
            ):
                raise ValueError(f"{label} must be a lowercase slug")
        if self.parent_prefix != self.prefix:
            raise ValueError("parent and NSCF prefixes must match")
        _positive_triplet(self.kpoint_grid, "kpoint_grid")
        if len(self.kpoint_offset) != 3 or any(
            type(value) is not int or value not in {0, 1}
            for value in self.kpoint_offset
        ):
            raise ValueError("kpoint_offset must contain three 0-or-1 shift flags")
        if type(self.band_count) is not int or self.band_count <= 0:
            raise ValueError("band_count must be positive")
        if type(self.occupations) is not QeNscfOccupations:
            raise TypeError("occupations must be a QeNscfOccupations")
        if type(self.verbosity) is not QeNscfVerbosity:
            raise TypeError("verbosity must be a QeNscfVerbosity")
        if type(self.diagonalization) is not QeNscfDiagonalization:
            raise TypeError("diagonalization must be a QeNscfDiagonalization")
        for label, boolean_value in (
            ("full_diagonalization_accuracy", self.full_diagonalization_accuracy),
            ("disable_symmetry", self.disable_symmetry),
            ("disable_time_reversal", self.disable_time_reversal),
        ):
            if type(boolean_value) is not bool:
                raise TypeError(f"{label} must be a boolean")
        _basename(self.input_filename, "input_filename")
        if self.input_filename == self.pseudopotential_filename:
            raise ValueError("input_filename must differ from the pseudopotential")
        if self.input_filename in {
            "artifact-manifest.json",
            "execution.json",
            "input-manifest.json",
            "nscf-saved-state-manifest.json",
            "parent-saved-state-manifest.json",
            "pw.err",
            "pw.out",
        }:
            raise ValueError("input_filename collides with a maintained artifact")
        if self.pseudo_dir != "./":
            raise ValueError("pseudo_dir must be ./ for exact local staging")
        if (
            type(self.outdir) is not str
            or not self.outdir
            or self.outdir != self.outdir.strip()
            or "'" in self.outdir
        ):
            raise ValueError("outdir must be nonempty, stripped, and unquoted")
        outdir = Path(self.outdir)
        if (
            outdir.is_absolute()
            or outdir in {Path("."), Path("")}
            or ".." in outdir.parts
        ):
            raise ValueError("outdir must be a safe non-current relative path")
        for label, precision_value in (
            ("coordinate_precision", self.coordinate_precision),
            ("kpoint_precision", self.kpoint_precision),
        ):
            if type(precision_value) is not int or precision_value <= 0:
                raise ValueError(f"{label} must be positive")
        if not self.qualification_statements or any(
            type(value) is not str or not value or value != value.strip()
            for value in self.qualification_statements
        ):
            raise ValueError("qualification_statements must be nonempty strings")
        self.projection_configuration()

    def projection_configuration(self) -> QeNscfProjectionConfiguration:
        """Extract typed projection state through the maintained QE hierarchy."""
        return QeNscfProjectionConfiguration(
            species=(
                QeAtomicSpecies(
                    symbol=self.pseudopotential_symbol,
                    mass_amu=self.pseudopotential_mass_amu,
                    pseudopotential_filename=self.pseudopotential_filename,
                ),
            ),
            kpoints=self.explicit_kpoints(),
            band_count=self.band_count,
            wavefunction_cutoff_ry=self.wavefunction_cutoff_ry,
            charge_density_cutoff_ry=self.charge_density_cutoff_ry,
            electronic_tolerance_ry=self.electronic_tolerance_ry,
            occupations=self.occupations,
            verbosity=self.verbosity,
            iprint=self.iprint,
            diagonalization=self.diagonalization,
            full_diagonalization_accuracy=self.full_diagonalization_accuracy,
            prefix=self.prefix,
            pseudo_dir=self.pseudo_dir,
            outdir=self.outdir,
            input_filename=self.input_filename,
            parent_saved_state_manifest_sha256=self.parent_manifest.sha256,
            disable_symmetry=self.disable_symmetry,
            disable_time_reversal=self.disable_time_reversal,
            coordinate_precision=self.coordinate_precision,
            kpoint_precision=self.kpoint_precision,
        )

    def explicit_kpoints(self) -> tuple[QeNscfKPoint, ...]:
        """Expand the configured grid in x-major, z-fastest source order."""
        first, second, third = self.kpoint_grid
        offset_first, offset_second, offset_third = self.kpoint_offset
        count = first * second * third
        weight = 1.0 / float(count)
        return tuple(
            QeNscfKPoint(
                coordinates=(
                    (float(index_first) + 0.5 * float(offset_first)) / float(first),
                    (float(index_second) + 0.5 * float(offset_second)) / float(second),
                    (float(index_third) + 0.5 * float(offset_third)) / float(third),
                ),
                weight=weight,
            )
            for index_first in range(first)
            for index_second in range(second)
            for index_third in range(third)
        )


def _path_text(value: str, label: str) -> None:
    if type(value) is not str or not value or value != value.strip() or "\0" in value:
        raise ValueError(f"{label} must be a nonempty stripped path")


def _sha256(value: str, label: str) -> None:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be lowercase SHA-256")


def _basename(value: str, label: str) -> None:
    if (
        type(value) is not str
        or not value
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
    ):
        raise ValueError(f"{label} must be a basename")


def _positive_triplet(value: tuple[int, int, int], label: str) -> None:
    if len(value) != 3 or any(type(item) is not int or item <= 0 for item in value):
        raise ValueError(f"{label} must contain three positive integers")
