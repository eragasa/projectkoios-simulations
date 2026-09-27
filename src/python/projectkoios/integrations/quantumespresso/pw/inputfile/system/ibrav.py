"""Typed Quantum ESPRESSO ``ibrav`` declarations and compatibility rules."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import IntEnum, StrEnum

from physkit.periodic import DirectLattice3D
from physkit.periodic.lattice.bravais3d import (
    BravaisLatticeKind,
)

QE_PW_INPUT_AUTHORITY = "https://www.quantum-espresso.org/Doc/INPUT_PW.html#id1"


class QeBravaisLattice(IntEnum):
    """Represent documented Quantum ESPRESSO ``ibrav`` values."""

    free = 0
    cubic_primitive = 1
    cubic_face_centered = 2
    cubic_body_centered = 3
    cubic_body_centered_symmetric = -3
    hexagonal_trigonal_primitive = 4
    trigonal_rhombohedral_axis_c = 5
    trigonal_rhombohedral_axis_111 = -5
    tetragonal_primitive = 6
    tetragonal_body_centered = 7
    orthorhombic_primitive = 8
    orthorhombic_base_centered = 9
    orthorhombic_base_centered_alternate = -9
    orthorhombic_one_face_base_centered = 91
    orthorhombic_face_centered = 10
    orthorhombic_body_centered = 11
    monoclinic_primitive_unique_c = 12
    monoclinic_primitive_unique_b = -12
    monoclinic_base_centered_unique_c = 13
    monoclinic_base_centered_unique_b = -13
    triclinic = 14

    @property
    def bravais_lattice_kind(self) -> BravaisLatticeKind:
        """Return the calculator-neutral lattice convention for this index."""
        return BravaisLatticeKind[self.name]


_REQUIRED_SHAPE_PARAMETERS: dict[
    QeBravaisLattice,
    tuple[frozenset[str], frozenset[str]],
] = {
    QeBravaisLattice.free: (frozenset(), frozenset()),
    QeBravaisLattice.cubic_primitive: (frozenset(), frozenset()),
    QeBravaisLattice.cubic_face_centered: (frozenset(), frozenset()),
    QeBravaisLattice.cubic_body_centered: (frozenset(), frozenset()),
    QeBravaisLattice.cubic_body_centered_symmetric: (frozenset(), frozenset()),
    QeBravaisLattice.hexagonal_trigonal_primitive: (
        frozenset({"celldm3"}),
        frozenset({"c"}),
    ),
    QeBravaisLattice.trigonal_rhombohedral_axis_c: (
        frozenset({"celldm4"}),
        frozenset({"cos_ab"}),
    ),
    QeBravaisLattice.trigonal_rhombohedral_axis_111: (
        frozenset({"celldm4"}),
        frozenset({"cos_ab"}),
    ),
    QeBravaisLattice.tetragonal_primitive: (
        frozenset({"celldm3"}),
        frozenset({"c"}),
    ),
    QeBravaisLattice.tetragonal_body_centered: (
        frozenset({"celldm3"}),
        frozenset({"c"}),
    ),
    QeBravaisLattice.orthorhombic_primitive: (
        frozenset({"celldm2", "celldm3"}),
        frozenset({"b", "c"}),
    ),
    QeBravaisLattice.orthorhombic_base_centered: (
        frozenset({"celldm2", "celldm3"}),
        frozenset({"b", "c"}),
    ),
    QeBravaisLattice.orthorhombic_base_centered_alternate: (
        frozenset({"celldm2", "celldm3"}),
        frozenset({"b", "c"}),
    ),
    QeBravaisLattice.orthorhombic_one_face_base_centered: (
        frozenset({"celldm2", "celldm3"}),
        frozenset({"b", "c"}),
    ),
    QeBravaisLattice.orthorhombic_face_centered: (
        frozenset({"celldm2", "celldm3"}),
        frozenset({"b", "c"}),
    ),
    QeBravaisLattice.orthorhombic_body_centered: (
        frozenset({"celldm2", "celldm3"}),
        frozenset({"b", "c"}),
    ),
    QeBravaisLattice.monoclinic_primitive_unique_c: (
        frozenset({"celldm2", "celldm3", "celldm4"}),
        frozenset({"b", "c", "cos_ab"}),
    ),
    QeBravaisLattice.monoclinic_primitive_unique_b: (
        frozenset({"celldm2", "celldm3", "celldm5"}),
        frozenset({"b", "c", "cos_ac"}),
    ),
    QeBravaisLattice.monoclinic_base_centered_unique_c: (
        frozenset({"celldm2", "celldm3", "celldm4"}),
        frozenset({"b", "c", "cos_ab"}),
    ),
    QeBravaisLattice.monoclinic_base_centered_unique_b: (
        frozenset({"celldm2", "celldm3", "celldm5"}),
        frozenset({"b", "c", "cos_ac"}),
    ),
    QeBravaisLattice.triclinic: (
        frozenset({"celldm2", "celldm3", "celldm4", "celldm5", "celldm6"}),
        frozenset({"b", "c", "cos_ab", "cos_ac", "cos_bc"}),
    ),
}


class QeCellParametersUnit(StrEnum):
    """Represent explicit units accepted by ``CELL_PARAMETERS``."""

    alat = "alat"
    bohr = "bohr"
    angstrom = "angstrom"


@dataclass(frozen=True, slots=True)
class QeCelldm:
    """Represent the ``celldm(1)`` through ``celldm(6)`` parameter family."""

    celldm1: float
    celldm2: float | None = None
    celldm3: float | None = None
    celldm4: float | None = None
    celldm5: float | None = None
    celldm6: float | None = None

    def __post_init__(self) -> None:
        _positive(self.celldm1, "celldm1")
        for value, label in (
            (self.celldm2, "celldm2"),
            (self.celldm3, "celldm3"),
        ):
            if value is not None:
                _positive(value, label)
        for value, label in (
            (self.celldm4, "celldm4"),
            (self.celldm5, "celldm5"),
            (self.celldm6, "celldm6"),
        ):
            if value is not None:
                _cosine(value, label)

    @property
    def has_shape_parameters(self) -> bool:
        """Return whether any value beyond ``celldm(1)`` is present."""
        return any(
            value is not None
            for value in (
                self.celldm2,
                self.celldm3,
                self.celldm4,
                self.celldm5,
                self.celldm6,
            )
        )


@dataclass(frozen=True, slots=True)
class QeLatticeParameters:
    """Represent the ``A, B, C, cosAB, cosAC, cosBC`` parameter family."""

    a: float
    b: float | None = None
    c: float | None = None
    cos_ab: float | None = None
    cos_ac: float | None = None
    cos_bc: float | None = None

    def __post_init__(self) -> None:
        _positive(self.a, "a")
        for value, label in ((self.b, "b"), (self.c, "c")):
            if value is not None:
                _positive(value, label)
        for value, label in (
            (self.cos_ab, "cos_ab"),
            (self.cos_ac, "cos_ac"),
            (self.cos_bc, "cos_bc"),
        ):
            if value is not None:
                _cosine(value, label)

    @property
    def has_shape_parameters(self) -> bool:
        """Return whether any value beyond ``A`` is present."""
        return any(
            value is not None
            for value in (self.b, self.c, self.cos_ab, self.cos_ac, self.cos_bc)
        )


@dataclass(frozen=True, slots=True)
class QeCellParameters:
    """Represent an explicit ``CELL_PARAMETERS`` card declaration."""

    vectors: DirectLattice3D
    unit: QeCellParametersUnit
    coordinate_precision: int

    def __post_init__(self) -> None:
        if not isinstance(self.vectors, DirectLattice3D):
            raise TypeError("vectors must be a DirectLattice3D")
        if type(self.unit) is not QeCellParametersUnit:
            raise TypeError("unit must be a QeCellParametersUnit")
        if type(self.coordinate_precision) is not int or self.coordinate_precision < 1:
            raise ValueError("coordinate_precision must be a positive integer")


@dataclass(frozen=True, slots=True)
class QeIbrav:
    """Validate one QE Bravais-lattice declaration before rendering input."""

    ibrav: QeBravaisLattice | None
    space_group: int | None = None
    celldm: QeCelldm | None = None
    lattice_parameters: QeLatticeParameters | None = None
    cell_parameters: QeCellParameters | None = None

    def __post_init__(self) -> None:
        if self.ibrav is not None and type(self.ibrav) is not QeBravaisLattice:
            raise TypeError("ibrav must be a QeBravaisLattice or None")
        if self.space_group is not None and (
            type(self.space_group) is not int or not 1 <= self.space_group <= 230
        ):
            raise ValueError("space_group must be an integer from 1 through 230")
        if self.celldm is not None and type(self.celldm) is not QeCelldm:
            raise TypeError("celldm must be a QeCelldm or None")
        if self.lattice_parameters is not None and (
            type(self.lattice_parameters) is not QeLatticeParameters
        ):
            raise TypeError("lattice_parameters must be a QeLatticeParameters or None")
        if self.cell_parameters is not None and (
            type(self.cell_parameters) is not QeCellParameters
        ):
            raise TypeError("cell_parameters must be a QeCellParameters or None")
        if self.ibrav is None:
            if self.space_group is None:
                raise ValueError("ibrav may be omitted only when space_group is set")
            self._reject_both_parameter_families()
            return
        if self.ibrav is QeBravaisLattice.free:
            self._validate_free_lattice()
            return
        self._validate_indexed_lattice()

    def _validate_free_lattice(self) -> None:
        if self.cell_parameters is None:
            raise ValueError("ibrav=0 requires CELL_PARAMETERS")
        self._reject_both_parameter_families()
        if self.celldm is not None and self.celldm.has_shape_parameters:
            raise ValueError("ibrav=0 permits only celldm(1), not celldm(2)-celldm(6)")
        if (
            self.lattice_parameters is not None
            and self.lattice_parameters.has_shape_parameters
        ):
            raise ValueError("ibrav=0 permits only A, not B, C, or angle cosines")

    def _validate_indexed_lattice(self) -> None:
        if self.cell_parameters is not None:
            raise ValueError("ibrav!=0 must not specify CELL_PARAMETERS")
        has_celldm = self.celldm is not None
        has_lattice_parameters = self.lattice_parameters is not None
        if has_celldm == has_lattice_parameters:
            raise ValueError(
                "ibrav!=0 requires exactly one of celldm or lattice_parameters"
            )
        ibrav = self.ibrav
        if ibrav is None or ibrav is QeBravaisLattice.free:
            raise RuntimeError("indexed-lattice validation requires nonzero ibrav")
        required_celldm, required_lattice = _REQUIRED_SHAPE_PARAMETERS[ibrav]
        if self.celldm is not None:
            _require_exact_parameters(
                _supplied_celldm_shape_parameters(self.celldm),
                required_celldm,
                "celldm",
            )
        if self.lattice_parameters is not None:
            _require_exact_parameters(
                _supplied_lattice_shape_parameters(self.lattice_parameters),
                required_lattice,
                "lattice_parameters",
            )

    def _reject_both_parameter_families(self) -> None:
        if self.celldm is not None and self.lattice_parameters is not None:
            raise ValueError("celldm and lattice_parameters are mutually exclusive")


def _supplied_celldm_shape_parameters(parameters: QeCelldm) -> frozenset[str]:
    values = {
        "celldm2": parameters.celldm2,
        "celldm3": parameters.celldm3,
        "celldm4": parameters.celldm4,
        "celldm5": parameters.celldm5,
        "celldm6": parameters.celldm6,
    }
    return frozenset(name for name, value in values.items() if value is not None)


def _supplied_lattice_shape_parameters(
    parameters: QeLatticeParameters,
) -> frozenset[str]:
    values = {
        "b": parameters.b,
        "c": parameters.c,
        "cos_ab": parameters.cos_ab,
        "cos_ac": parameters.cos_ac,
        "cos_bc": parameters.cos_bc,
    }
    return frozenset(name for name, value in values.items() if value is not None)


def _require_exact_parameters(
    supplied: frozenset[str],
    required: frozenset[str],
    family: str,
) -> None:
    if supplied != required:
        missing = sorted(required - supplied)
        unexpected = sorted(supplied - required)
        raise ValueError(
            f"{family} does not match ibrav requirements: "
            f"missing={missing}, unexpected={unexpected}"
        )


def _positive(value: float, label: str) -> None:
    if type(value) is not float or not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{label} must be a positive finite float")


def _cosine(value: float, label: str) -> None:
    if type(value) is not float or not math.isfinite(value) or not -1.0 < value < 1.0:
        raise ValueError(f"{label} must be a finite float strictly between -1 and 1")
