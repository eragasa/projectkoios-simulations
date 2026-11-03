"""Immutable mechanically faithful QEXSD source and document values."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import ClassVar

type Vector3 = tuple[float, float, float]
type Vector3Sequence = tuple[Vector3, ...]
type SpeciesDeclaration = tuple[str, float, str]
type AtomDeclaration = tuple[int, str, Vector3]
type Spectrum = tuple[tuple[float, ...], ...]


@dataclass(frozen=True, slots=True)
class QexsdSource:
    """Explicit QEXSD bytes and verified external source identity.

    Attributes
    ----------
    canonical_path
        Canonical absolute POSIX path identifying the independently obtained source.
    sha256
        Lowercase SHA-256 digest of the exact source bytes.
    byte_count
        Number of exact source bytes in the unsigned 64-bit range.
    content
        Exact immutable XML bytes supplied to the parser.
    """

    _SHA256: ClassVar[re.Pattern[str]] = re.compile(r"[0-9a-f]{64}\Z")

    canonical_path: str
    sha256: str
    byte_count: int
    content: bytes

    def __post_init__(self) -> None:
        if type(self.canonical_path) is not str:
            raise TypeError("canonical_path must be a built-in str")
        path = PurePosixPath(self.canonical_path)
        if (
            not self.canonical_path.startswith("/")
            or self.canonical_path.startswith("//")
            or str(path) != self.canonical_path
            or any(part in {"", ".", ".."} for part in path.parts[1:])
        ):
            raise ValueError("canonical_path must be a canonical absolute POSIX path")
        if type(self.sha256) is not str:
            raise TypeError("sha256 must be a built-in str")
        if self._SHA256.fullmatch(self.sha256) is None:
            raise ValueError("sha256 must be lowercase SHA-256")
        if type(self.byte_count) is not int:
            raise TypeError("byte_count must be a built-in integer excluding bool")
        if self.byte_count < 0:
            raise ValueError("byte_count must be nonnegative")
        if type(self.content) is not bytes:
            raise TypeError("content must be built-in bytes")
        if (
            len(self.content) != self.byte_count
            or hashlib.sha256(self.content).hexdigest() != self.sha256
        ):
            raise ValueError("QEXSD source identity mismatch")


@dataclass(frozen=True, slots=True)
class QexsdDocument:
    """Mechanically parsed raw values in exact QEXSD source order.

    Labels describe source locations only. No unit, coordinate, scale, weight,
    spin, or energy-reference interpretation is performed here.

    Attributes
    ----------
    source_path, source_sha256, source_byte_count
        Canonical source path and retained byte-identity observations.
    namespace, qexsd_version
        Exact native XML namespace and format version.
    producing_application, producing_application_version
        Native producer labels, with version optionally unavailable.
    declared_unit_system_label
        Uninterpreted native unit-system declaration.
    atomic_structure_alat
        Positive finite built-in float as represented by QEXSD.
    direct_lattice_vectors, reciprocal_lattice_coefficients
        Three source-ordered finite built-in-float vectors.
    species, atoms
        Ordered native declarations with resolvable species references.
    declared_atom_count
        Positive built-in integer equal to the atom declaration count.
    k_points, k_point_weights, sampled_k_point_count
        Ordered native sampling arrays and their declared positive count.
    eigenvalues, occupations, band_count
        Ordered finite spectral rows, optional occupation rows, and positive band
        count with exact represented shape agreement.
    total_energy
        Finite built-in-float native total-energy value.
    fft_grid, fft_smooth, fft_box
        Positive built-in-integer native FFT triplets.
    exit_status
        Built-in integer in the inclusive range 0 through 255.
    direct_lattice_source_label, reciprocal_lattice_source_label,
    atomic_positions_source_label, k_point_source_label,
    eigenvalue_source_label, total_energy_source_label
        Nonempty source-location labels without semantic conversion.
    """

    _SHA256: ClassVar[re.Pattern[str]] = re.compile(r"[0-9a-f]{64}\Z")

    source_path: str
    source_sha256: str
    source_byte_count: int
    namespace: str
    qexsd_version: str
    producing_application: str
    producing_application_version: str | None
    declared_unit_system_label: str
    atomic_structure_alat: float
    direct_lattice_vectors: Vector3Sequence
    direct_lattice_source_label: str
    reciprocal_lattice_coefficients: Vector3Sequence
    reciprocal_lattice_source_label: str
    species: tuple[SpeciesDeclaration, ...]
    atoms: tuple[AtomDeclaration, ...]
    declared_atom_count: int
    atomic_positions_source_label: str
    k_points: Vector3Sequence
    k_point_weights: tuple[float, ...]
    sampled_k_point_count: int
    k_point_source_label: str
    eigenvalues: Spectrum
    occupations: Spectrum | None
    eigenvalue_source_label: str
    band_count: int
    total_energy: float
    total_energy_source_label: str
    fft_grid: tuple[int, int, int]
    fft_smooth: tuple[int, int, int]
    fft_box: tuple[int, int, int]
    exit_status: int

    def __post_init__(self) -> None:
        string_fields = (
            "source_path",
            "source_sha256",
            "namespace",
            "qexsd_version",
            "producing_application",
            "declared_unit_system_label",
            "direct_lattice_source_label",
            "reciprocal_lattice_source_label",
            "atomic_positions_source_label",
            "k_point_source_label",
            "eigenvalue_source_label",
            "total_energy_source_label",
        )
        for name in string_fields:
            value = getattr(self, name)
            if type(value) is not str:
                raise TypeError(f"{name} must be a built-in str")
            if not value:
                raise ValueError(f"{name} must be nonempty")
        path = PurePosixPath(self.source_path)
        if (
            not self.source_path.startswith("/")
            or self.source_path.startswith("//")
            or str(path) != self.source_path
            or any(part in {"", ".", ".."} for part in path.parts[1:])
        ):
            raise ValueError("source_path must be a canonical absolute POSIX path")
        if self._SHA256.fullmatch(self.source_sha256) is None:
            raise ValueError("source_sha256 must be lowercase SHA-256")
        if type(self.source_byte_count) is not int:
            raise TypeError("source_byte_count must be a built-in integer")
        if self.source_byte_count < 0:
            raise ValueError("source_byte_count must be nonnegative")
        if self.producing_application_version is not None:
            if type(self.producing_application_version) is not str:
                raise TypeError("producing_application_version must be str or None")
            if not self.producing_application_version:
                raise ValueError("producing_application_version must be nonempty")
        if type(self.atomic_structure_alat) is not float:
            raise TypeError("atomic_structure_alat must be a built-in float")
        if (
            not math.isfinite(self.atomic_structure_alat)
            or self.atomic_structure_alat <= 0
        ):
            raise ValueError("atomic_structure_alat must be positive and finite")
        self._vectors(self.direct_lattice_vectors, "direct lattice", 3)
        self._vectors(self.reciprocal_lattice_coefficients, "reciprocal lattice", 3)
        self._vectors(self.k_points, "k points", None)
        if type(self.species) is not tuple:
            raise TypeError("species must be a tuple")
        if not self.species:
            raise ValueError("species must be nonempty")
        for item in self.species:
            if type(item) is not tuple:
                raise TypeError("species declarations must be tuples")
            if len(item) != 3:
                raise ValueError("species declarations must contain three fields")
            name, mass, label = item
            if type(name) is not str or type(label) is not str:
                raise TypeError("species names and labels must be strings")
            if not name or not label:
                raise ValueError("species names and labels must be nonempty")
            if type(mass) is not float:
                raise TypeError("species mass must be a built-in float")
            if not math.isfinite(mass) or mass <= 0:
                raise ValueError("species mass must be positive and finite")
        species_names = tuple(item[0] for item in self.species)
        if len(set(species_names)) != len(species_names):
            raise ValueError("species names must be unique")
        self._positive_integer(self.declared_atom_count, "declared_atom_count")
        if type(self.atoms) is not tuple:
            raise TypeError("atoms must be a tuple")
        if len(self.atoms) != self.declared_atom_count:
            raise ValueError("atom count disagrees")
        for expected, atom in enumerate(self.atoms, start=1):
            if type(atom) is not tuple:
                raise TypeError("atom declarations must be tuples")
            if len(atom) != 3:
                raise ValueError("atom declarations must contain three fields")
            if type(atom[0]) is not int or type(atom[1]) is not str:
                raise TypeError("atom index and species reference have wrong types")
            if atom[0] != expected or atom[1] not in species_names:
                raise ValueError("atom ordering or species reference is invalid")
            self._vector(atom[2], "atomic position")
        self._positive_integer(self.sampled_k_point_count, "sampled_k_point_count")
        if type(self.k_point_weights) is not tuple:
            raise TypeError("k_point_weights must be a tuple")
        if len(self.k_point_weights) != len(
            self.k_points
        ) or self.sampled_k_point_count != len(self.k_points):
            raise ValueError("k-point counts disagree")
        if any(type(value) is not float for value in self.k_point_weights):
            raise TypeError("k-point weights must be built-in floats")
        if any(not math.isfinite(value) or value < 0 for value in self.k_point_weights):
            raise ValueError("k-point weights must be finite and nonnegative")
        self._positive_integer(self.band_count, "band_count")
        if type(self.eigenvalues) is not tuple:
            raise TypeError("eigenvalues must be a tuple")
        if len(self.eigenvalues) != len(self.k_points):
            raise ValueError("eigenvalue and k-point counts disagree")
        for row in self.eigenvalues:
            self._row(row, "eigenvalues")
            if len(row) != self.band_count:
                raise ValueError("eigenvalue band counts disagree")
        if self.occupations is not None:
            if type(self.occupations) is not tuple:
                raise TypeError("occupations must be a tuple or None")
            if len(self.occupations) != len(self.eigenvalues):
                raise ValueError("occupation shape disagrees")
            for occupations, eigenvalues in zip(
                self.occupations, self.eigenvalues, strict=True
            ):
                self._row(occupations, "occupations")
                if len(occupations) != len(eigenvalues):
                    raise ValueError("occupation shape disagrees")
        if type(self.total_energy) is not float:
            raise TypeError("total_energy must be a built-in float")
        if not math.isfinite(self.total_energy):
            raise ValueError("total_energy must be finite")
        for name in ("fft_grid", "fft_smooth", "fft_box"):
            grid = getattr(self, name)
            if type(grid) is not tuple:
                raise TypeError(f"{name} must be a tuple")
            if len(grid) != 3:
                raise ValueError(f"{name} must contain three values")
            if any(type(value) is not int for value in grid):
                raise TypeError(f"{name} values must be built-in integers")
            if any(value <= 0 for value in grid):
                raise ValueError(f"{name} values must be positive")
        if type(self.exit_status) is not int:
            raise TypeError("exit_status must be a built-in integer")
        if not 0 <= self.exit_status <= 255:
            raise ValueError("exit_status must be in 0..255")

    @staticmethod
    def _positive_integer(value: int, name: str) -> None:
        if type(value) is not int:
            raise TypeError(f"{name} must be a built-in integer")
        if value <= 0:
            raise ValueError(f"{name} must be positive")

    @classmethod
    def _vectors(cls, vectors: Vector3Sequence, name: str, count: int | None) -> None:
        if type(vectors) is not tuple:
            raise TypeError(f"{name} vectors must be a tuple")
        if count is not None and len(vectors) != count:
            raise ValueError(f"{name} must contain exactly {count} vectors")
        for vector in vectors:
            cls._vector(vector, name)

    @staticmethod
    def _vector(vector: Vector3, name: str) -> None:
        if type(vector) is not tuple:
            raise TypeError(f"{name} must be a tuple")
        if len(vector) != 3:
            raise ValueError(f"{name} must contain three components")
        if any(type(value) is not float for value in vector):
            raise TypeError(f"{name} components must be built-in floats")
        if any(not math.isfinite(value) for value in vector):
            raise ValueError(f"{name} components must be finite")

    @staticmethod
    def _row(row: tuple[float, ...], name: str) -> None:
        if type(row) is not tuple:
            raise TypeError(f"{name} rows must be tuples")
        if not row:
            raise ValueError(f"{name} rows must be nonempty")
        if any(type(value) is not float for value in row):
            raise TypeError(f"{name} values must be built-in floats")
        if any(not math.isfinite(value) for value in row):
            raise ValueError(f"{name} values must be finite")
