"""Calculator-neutral supercell construction and site substitution actions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import product

import numpy as np

from projectkoios.physkit.core.actions import DataObjectActionizer
from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.core.results import ResultsObject
from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.physkit.periodic.unit_cell import Atom, AtomicBasis, UnitCell
from projectkoios.physkit.units import Unitless, VectorQuantity

_ELEMENT_SYMBOL = re.compile(r"[A-Z][a-z]?")

type SuperCellRepetitions = tuple[int, int, int]
type UnitCellTranslation = tuple[int, int, int]


@dataclass(frozen=True, slots=True, kw_only=True)
class UnitCellSiteOrigin(DataObject):
    """Identify one replicated site by source index and cell translation."""

    source_atom_index: int
    translation: UnitCellTranslation

    def __post_init__(self) -> None:
        if type(self.source_atom_index) is not int:
            raise TypeError("source_atom_index must be a built-in int")
        if self.source_atom_index < 0:
            raise ValueError("source_atom_index must be nonnegative")
        _validate_integer_triplet(
            self.translation,
            label="translation",
            require_positive=False,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class SuperCell(UnitCell):
    """Retain a replicated unit cell and exact source-site provenance."""

    source_unit_cell: UnitCell
    repetitions: SuperCellRepetitions
    site_origins: tuple[UnitCellSiteOrigin, ...]

    def __post_init__(self) -> None:
        UnitCell.__post_init__(self)
        if not isinstance(self.source_unit_cell, UnitCell):
            raise TypeError("source_unit_cell must be a UnitCell")
        _validate_integer_triplet(
            self.repetitions,
            label="repetitions",
            require_positive=True,
        )
        if type(self.site_origins) is not tuple or any(
            type(origin) is not UnitCellSiteOrigin for origin in self.site_origins
        ):
            raise TypeError("site_origins must be a tuple of UnitCellSiteOrigin values")
        _validate_supercell_geometry(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class SuperCellConstructionRequest(DataObject):
    """Request diagonal replication of one source unit cell."""

    source_unit_cell: UnitCell
    repetitions: SuperCellRepetitions

    def __post_init__(self) -> None:
        if not isinstance(self.source_unit_cell, UnitCell):
            raise TypeError("source_unit_cell must be a UnitCell")
        _validate_integer_triplet(
            self.repetitions,
            label="repetitions",
            require_positive=True,
        )
        for atom in self.source_unit_cell.atomic_basis.atoms:
            coordinates = atom.position_fractional.magnitude
            if np.any(coordinates < 0.0) or np.any(coordinates >= 1.0):
                raise ValueError(
                    "source fractional coordinates must lie in the half-open "
                    "interval [0, 1)"
                )


@dataclass(frozen=True, slots=True, kw_only=True)
class SuperCellConstructionResult(ResultsObject):
    """Correlate a construction request with its pristine supercell."""

    request: SuperCellConstructionRequest
    supercell: SuperCell

    def __post_init__(self) -> None:
        if type(self.request) is not SuperCellConstructionRequest:
            raise TypeError("request must be a SuperCellConstructionRequest")
        if type(self.supercell) is not SuperCell:
            raise TypeError("supercell must be a SuperCell")
        if self.supercell.source_unit_cell is not self.request.source_unit_cell:
            raise ValueError("supercell must retain the exact requested source cell")
        if self.supercell.repetitions != self.request.repetitions:
            raise ValueError("supercell repetitions must match the request")
        _validate_pristine_replication(self.supercell)


class SuperCellBuilder(
    DataObjectActionizer[SuperCellConstructionRequest, SuperCellConstructionResult]
):
    """Build one diagonal supercell with deterministic site provenance."""

    __slots__ = ()

    def action(
        self,
        *,
        request: SuperCellConstructionRequest,
    ) -> SuperCellConstructionResult:
        """Replicate the requested cell without calculator-specific behavior."""
        if type(request) is not SuperCellConstructionRequest:
            raise TypeError("request must be a SuperCellConstructionRequest")

        repetitions = np.asarray(request.repetitions, dtype=np.float64)
        source_matrix = request.source_unit_cell.A.magnitude
        supercell_matrix = source_matrix * repetitions[np.newaxis, :]
        direct_lattice = DirectLattice3D(
            a1=supercell_matrix[:, 0],
            a2=supercell_matrix[:, 1],
            a3=supercell_matrix[:, 2],
        )

        atoms: list[Atom] = []
        origins: list[UnitCellSiteOrigin] = []
        for translation in _translations(request.repetitions):
            translation_vector = np.asarray(translation, dtype=np.float64)
            for source_atom_index, atom in enumerate(
                request.source_unit_cell.atomic_basis.atoms
            ):
                atoms.append(
                    Atom(
                        symbol=atom.symbol,
                        position_fractional=VectorQuantity(
                            magnitude=(
                                atom.position_fractional.magnitude + translation_vector
                            )
                            / repetitions,
                            unit=Unitless(),
                        ),
                    )
                )
                origins.append(
                    UnitCellSiteOrigin(
                        source_atom_index=source_atom_index,
                        translation=translation,
                    )
                )

        supercell = SuperCell(
            direct_lattice=direct_lattice,
            lattice_parameter=request.source_unit_cell.lattice_parameter,
            atomic_basis=AtomicBasis(atoms=tuple(atoms)),
            source_unit_cell=request.source_unit_cell,
            repetitions=request.repetitions,
            site_origins=tuple(origins),
        )
        return SuperCellConstructionResult(request=request, supercell=supercell)


@dataclass(frozen=True, slots=True, kw_only=True)
class SuperCellSubstitutionRequest(DataObject):
    """Request replacement of one provenance-identified supercell site."""

    supercell: SuperCell
    source_atom_index: int
    translation: UnitCellTranslation
    replacement_symbol: str

    def __post_init__(self) -> None:
        if type(self.supercell) is not SuperCell:
            raise TypeError("supercell must be a SuperCell")
        target = UnitCellSiteOrigin(
            source_atom_index=self.source_atom_index,
            translation=self.translation,
        )
        if target not in self.supercell.site_origins:
            raise ValueError("requested source site and translation are not present")
        if type(self.replacement_symbol) is not str or not _ELEMENT_SYMBOL.fullmatch(
            self.replacement_symbol
        ):
            raise ValueError("replacement_symbol must be an element symbol")
        target_index = self.supercell.site_origins.index(target)
        source_symbol = self.supercell.atomic_basis.atoms[target_index].symbol
        if self.replacement_symbol == source_symbol:
            raise ValueError("replacement_symbol must differ from the source symbol")


@dataclass(frozen=True, slots=True, kw_only=True)
class SuperCellSubstitutionResult(ResultsObject):
    """Correlate one site-substitution request with its resulting supercell."""

    request: SuperCellSubstitutionRequest
    supercell: SuperCell
    substituted_atom_index: int

    def __post_init__(self) -> None:
        if type(self.request) is not SuperCellSubstitutionRequest:
            raise TypeError("request must be a SuperCellSubstitutionRequest")
        if type(self.supercell) is not SuperCell:
            raise TypeError("supercell must be a SuperCell")
        if type(self.substituted_atom_index) is not int:
            raise TypeError("substituted_atom_index must be a built-in int")
        _validate_substitution_result(self)


class SuperCellSubstitutor(
    DataObjectActionizer[SuperCellSubstitutionRequest, SuperCellSubstitutionResult]
):
    """Replace exactly one provenance-identified supercell site."""

    __slots__ = ()

    def action(
        self,
        *,
        request: SuperCellSubstitutionRequest,
    ) -> SuperCellSubstitutionResult:
        """Return a supercell differing only at the requested chemical symbol."""
        if type(request) is not SuperCellSubstitutionRequest:
            raise TypeError("request must be a SuperCellSubstitutionRequest")
        target = UnitCellSiteOrigin(
            source_atom_index=request.source_atom_index,
            translation=request.translation,
        )
        target_index = request.supercell.site_origins.index(target)
        atoms = list(request.supercell.atomic_basis.atoms)
        source_atom = atoms[target_index]
        atoms[target_index] = Atom(
            symbol=request.replacement_symbol,
            position_fractional=source_atom.position_fractional,
        )
        supercell = SuperCell(
            direct_lattice=request.supercell.direct_lattice,
            lattice_parameter=request.supercell.lattice_parameter,
            atomic_basis=AtomicBasis(atoms=tuple(atoms)),
            source_unit_cell=request.supercell.source_unit_cell,
            repetitions=request.supercell.repetitions,
            site_origins=request.supercell.site_origins,
        )
        return SuperCellSubstitutionResult(
            request=request,
            supercell=supercell,
            substituted_atom_index=target_index,
        )


def _validate_integer_triplet(
    values: object,
    *,
    label: str,
    require_positive: bool,
) -> None:
    if not (
        type(values) is tuple
        and len(values) == 3
        and all(type(value) is int for value in values)
    ):
        raise TypeError(f"{label} must be a three-tuple of built-in ints")
    minimum = 1 if require_positive else 0
    if any(value < minimum for value in values):
        qualifier = "positive" if require_positive else "nonnegative"
        raise ValueError(f"{label} values must be {qualifier}")


def _translations(
    repetitions: SuperCellRepetitions,
) -> tuple[UnitCellTranslation, ...]:
    return tuple(
        (first, second, third)
        for first, second, third in product(
            range(repetitions[0]),
            range(repetitions[1]),
            range(repetitions[2]),
        )
    )


def _validate_supercell_geometry(supercell: SuperCell) -> None:
    source_cell = supercell.source_unit_cell
    repetitions = supercell.repetitions
    expected_matrix = (
        source_cell.A.magnitude
        * np.asarray(
            repetitions,
            dtype=np.float64,
        )[np.newaxis, :]
    )
    if not np.array_equal(supercell.A.magnitude, expected_matrix):
        raise ValueError("supercell lattice must be the declared diagonal replication")
    if supercell.lattice_parameter != source_cell.lattice_parameter:
        raise ValueError("supercell must retain the source lattice parameter")

    source_atoms = source_cell.atomic_basis.atoms
    expected_count = len(source_atoms) * int(np.prod(repetitions))
    actual_atoms = supercell.atomic_basis.atoms
    if (
        len(actual_atoms) != expected_count
        or len(supercell.site_origins) != expected_count
    ):
        raise ValueError("supercell atom and provenance counts must match replication")

    repetitions_array = np.asarray(repetitions, dtype=np.float64)
    index = 0
    for translation in _translations(repetitions):
        translation_array = np.asarray(translation, dtype=np.float64)
        for source_atom_index, source_atom in enumerate(source_atoms):
            expected_origin = UnitCellSiteOrigin(
                source_atom_index=source_atom_index,
                translation=translation,
            )
            if supercell.site_origins[index] != expected_origin:
                raise ValueError("site_origins must retain deterministic source order")
            expected_position = (
                source_atom.position_fractional.magnitude + translation_array
            ) / repetitions_array
            if not np.array_equal(
                actual_atoms[index].position_fractional.magnitude,
                expected_position,
            ):
                raise ValueError("supercell positions must exactly match replication")
            index += 1


def _validate_pristine_replication(supercell: SuperCell) -> None:
    source_atoms = supercell.source_unit_cell.atomic_basis.atoms
    for atom, origin in zip(
        supercell.atomic_basis.atoms,
        supercell.site_origins,
        strict=True,
    ):
        if atom.symbol != source_atoms[origin.source_atom_index].symbol:
            raise ValueError(
                "constructed pristine supercell must retain source symbols"
            )


def _validate_substitution_result(result: SuperCellSubstitutionResult) -> None:
    source_cell = result.request.supercell
    target = UnitCellSiteOrigin(
        source_atom_index=result.request.source_atom_index,
        translation=result.request.translation,
    )
    expected_index = source_cell.site_origins.index(target)
    if result.substituted_atom_index != expected_index:
        raise ValueError("substituted_atom_index must identify the requested site")
    if result.supercell.source_unit_cell is not source_cell.source_unit_cell:
        raise ValueError("substitution must retain the exact source unit cell")
    if result.supercell.repetitions != source_cell.repetitions:
        raise ValueError("substitution must retain supercell repetitions")
    if result.supercell.site_origins != source_cell.site_origins:
        raise ValueError("substitution must retain site provenance")

    source_atoms = source_cell.atomic_basis.atoms
    result_atoms = result.supercell.atomic_basis.atoms
    for atom_index, (source_atom, result_atom) in enumerate(
        zip(source_atoms, result_atoms, strict=True)
    ):
        expected_symbol = (
            result.request.replacement_symbol
            if atom_index == expected_index
            else source_atom.symbol
        )
        if result_atom.symbol != expected_symbol or not np.array_equal(
            result_atom.position_fractional.magnitude,
            source_atom.position_fractional.magnitude,
        ):
            raise ValueError("substitution may change only the requested site symbol")
