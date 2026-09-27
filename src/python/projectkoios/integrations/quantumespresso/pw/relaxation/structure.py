"""Extract calculator-neutral final structures from parsed QEXSD documents."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Protocol, cast

import numpy as np
from physkit.periodic.lattice import DirectLattice3D
from physkit.periodic.unit_cell import Atom, AtomicBasis, UnitCell
from physkit.units import PhysicalUnit, ScalarQuantity, Unitless, VectorQuantity

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_REQUIRED_DOCUMENT_FIELDS = (
    "source_path",
    "source_sha256",
    "source_byte_count",
    "qexsd_version",
    "producing_application",
    "producing_application_version",
    "declared_unit_system_label",
    "atomic_structure_alat",
    "direct_lattice_vectors",
    "direct_lattice_source_label",
    "atoms",
    "declared_atom_count",
    "atomic_positions_source_label",
    "exit_status",
)

type _Vector3 = tuple[float, float, float]
type _AtomDeclaration = tuple[int, str, _Vector3]


class _QexsdStructureDocument(Protocol):
    source_path: str
    source_sha256: str
    source_byte_count: int
    qexsd_version: str
    producing_application: str
    producing_application_version: str | None
    declared_unit_system_label: str
    atomic_structure_alat: float
    direct_lattice_vectors: tuple[_Vector3, ...]
    direct_lattice_source_label: str
    atoms: tuple[_AtomDeclaration, ...]
    declared_atom_count: int
    atomic_positions_source_label: str
    exit_status: int


@dataclass(frozen=True, slots=True)
class QeQexsdFinalStructure:
    """Retain an observed final structure and its QEXSD source identity."""

    unit_cell: UnitCell
    source_path: str
    source_sha256: str
    source_byte_count: int
    qexsd_version: str
    producing_application: str
    producing_application_version: str | None
    exit_status: int
    direct_lattice_source_label: str
    atomic_positions_source_label: str
    transformation: str

    def __post_init__(self) -> None:
        if type(self.unit_cell) is not UnitCell:
            raise TypeError("unit_cell must be a UnitCell")
        for label, value in (
            ("source_path", self.source_path),
            ("qexsd_version", self.qexsd_version),
            ("producing_application", self.producing_application),
            ("direct_lattice_source_label", self.direct_lattice_source_label),
            ("atomic_positions_source_label", self.atomic_positions_source_label),
            ("transformation", self.transformation),
        ):
            if type(value) is not str or not value:
                raise ValueError(f"{label} must be a nonempty string")
        if (
            type(self.source_sha256) is not str
            or _SHA256.fullmatch(self.source_sha256) is None
        ):
            raise ValueError("source_sha256 must be lowercase SHA-256")
        if type(self.source_byte_count) is not int or self.source_byte_count < 0:
            raise ValueError("source_byte_count must be a nonnegative integer")
        if self.producing_application_version is not None and (
            type(self.producing_application_version) is not str
            or not self.producing_application_version
        ):
            raise ValueError("producing_application_version must be nonempty or None")
        if type(self.exit_status) is not int or not 0 <= self.exit_status <= 255:
            raise ValueError("exit_status must be an integer in 0..255")


@dataclass(frozen=True, slots=True)
class QeQexsdFinalStructureExtractor:
    """Convert structure values emitted by the maintained ksdft2effmass parser."""

    def extract(self, document: object) -> QeQexsdFinalStructure:
        """Extract a PhysKit unit cell without parsing or rediscovering XML."""
        if any(not hasattr(document, name) for name in _REQUIRED_DOCUMENT_FIELDS):
            raise TypeError(
                "document must be a QexsdDocument produced by "
                "QuantumEspressoXsdDocumentParser"
            )
        parsed = cast("_QexsdStructureDocument", document)
        if parsed.declared_unit_system_label != "Hartree atomic units":
            raise ValueError("unsupported QEXSD declared unit system")
        if (
            type(parsed.atomic_structure_alat) is not float
            or not math.isfinite(parsed.atomic_structure_alat)
            or parsed.atomic_structure_alat <= 0.0
        ):
            raise ValueError("atomic_structure_alat must be positive and finite")
        if (
            type(parsed.direct_lattice_vectors) is not tuple
            or len(parsed.direct_lattice_vectors) != 3
        ):
            raise ValueError("direct_lattice_vectors must contain three vectors")
        direct_vectors = np.asarray(parsed.direct_lattice_vectors, dtype=np.float64)
        if direct_vectors.shape != (3, 3) or not np.isfinite(direct_vectors).all():
            raise ValueError("direct_lattice_vectors must be a finite 3 by 3 array")
        physical_cell = direct_vectors.T
        if math.isclose(float(np.linalg.det(physical_cell)), 0.0, abs_tol=1.0e-15):
            raise ValueError("direct_lattice_vectors must be nonsingular")
        if type(parsed.atoms) is not tuple or len(parsed.atoms) != (
            parsed.declared_atom_count
        ):
            raise ValueError("QEXSD atom count disagrees with atom declarations")

        fractional_atoms: list[Atom] = []
        for expected_index, declaration in enumerate(parsed.atoms, start=1):
            if type(declaration) is not tuple or len(declaration) != 3:
                raise ValueError("QEXSD atom declarations must contain three fields")
            index, symbol, cartesian = declaration
            if index != expected_index:
                raise ValueError("QEXSD atom declarations must retain source order")
            cartesian_vector = np.asarray(cartesian, dtype=np.float64)
            if (
                cartesian_vector.shape != (3,)
                or not np.isfinite(cartesian_vector).all()
            ):
                raise ValueError("QEXSD atomic positions must be finite three-vectors")
            fractional_atoms.append(
                Atom(
                    symbol=symbol,
                    position_fractional=VectorQuantity(
                        magnitude=np.linalg.solve(physical_cell, cartesian_vector),
                        unit=Unitless(),
                    ),
                )
            )

        alat = parsed.atomic_structure_alat
        unit_cell = UnitCell(
            direct_lattice=DirectLattice3D(
                a1=physical_cell[:, 0] / alat,
                a2=physical_cell[:, 1] / alat,
                a3=physical_cell[:, 2] / alat,
            ),
            lattice_parameter=ScalarQuantity(
                magnitude=alat,
                unit=PhysicalUnit("bohr"),
            ),
            atomic_basis=AtomicBasis(atoms=tuple(fractional_atoms)),
        )
        return QeQexsdFinalStructure(
            unit_cell=unit_cell,
            source_path=parsed.source_path,
            source_sha256=parsed.source_sha256,
            source_byte_count=parsed.source_byte_count,
            qexsd_version=parsed.qexsd_version,
            producing_application=parsed.producing_application,
            producing_application_version=parsed.producing_application_version,
            exit_status=parsed.exit_status,
            direct_lattice_source_label=parsed.direct_lattice_source_label,
            atomic_positions_source_label=parsed.atomic_positions_source_label,
            transformation=(
                "ksdft2effmass QEXSD Cartesian direct vectors and atomic positions "
                "in bohr; fractional positions solved against the source-ordered "
                "cell; no vector reordering or coordinate wrapping"
            ),
        )
