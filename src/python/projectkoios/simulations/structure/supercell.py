"""Calculator-neutral diagonal supercell construction contracts."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np

from projectkoios.physkit.core.actions import DataObjectActionizer
from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.core.results import ResultsObject
from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.physkit.periodic.unit_cell import Atom, AtomicBasis, UnitCell
from projectkoios.physkit.units import Unitless, VectorQuantity

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
        if not (
            type(self.translation) is tuple
            and len(self.translation) == 3
            and all(type(value) is int for value in self.translation)
        ):
            raise TypeError("translation must be a three-tuple of built-in ints")
        if any(value < 0 for value in self.translation):
            raise ValueError("translation values must be nonnegative")


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
        if not (
            type(self.repetitions) is tuple
            and len(self.repetitions) == 3
            and all(type(value) is int for value in self.repetitions)
        ):
            raise TypeError("repetitions must be a three-tuple of built-in ints")
        if any(value < 1 for value in self.repetitions):
            raise ValueError("repetitions values must be positive")
        if type(self.site_origins) is not tuple or any(
            type(origin) is not UnitCellSiteOrigin for origin in self.site_origins
        ):
            raise TypeError("site_origins must be a tuple of UnitCellSiteOrigin values")

        source_cell = self.source_unit_cell
        repetitions = self.repetitions
        expected_matrix = (
            source_cell.A.magnitude
            * np.asarray(repetitions, dtype=np.float64)[np.newaxis, :]
        )
        if not np.array_equal(self.A.magnitude, expected_matrix):
            raise ValueError(
                "supercell lattice must be the declared diagonal replication"
            )
        if self.lattice_parameter != source_cell.lattice_parameter:
            raise ValueError("supercell must retain the source lattice parameter")
        source_atoms = source_cell.atomic_basis.atoms
        expected_count = len(source_atoms) * int(np.prod(repetitions))
        actual_atoms = self.atomic_basis.atoms
        if (
            len(actual_atoms) != expected_count
            or len(self.site_origins) != expected_count
        ):
            raise ValueError(
                "supercell atom and provenance counts must match replication"
            )
        repetitions_array = np.asarray(repetitions, dtype=np.float64)
        index = 0
        for translation in product(
            range(repetitions[0]),
            range(repetitions[1]),
            range(repetitions[2]),
        ):
            translation_array = np.asarray(translation, dtype=np.float64)
            for source_atom_index, source_atom in enumerate(source_atoms):
                if self.site_origins[index] != UnitCellSiteOrigin(
                    source_atom_index=source_atom_index,
                    translation=translation,
                ):
                    raise ValueError(
                        "site_origins must retain deterministic source order"
                    )
                expected_position = (
                    source_atom.position_fractional.magnitude + translation_array
                ) / repetitions_array
                if not np.array_equal(
                    actual_atoms[index].position_fractional.magnitude,
                    expected_position,
                ):
                    raise ValueError(
                        "supercell positions must exactly match replication"
                    )
                index += 1


@dataclass(frozen=True, slots=True, kw_only=True)
class SuperCellConstructionRequest(DataObject):
    """Request diagonal replication of one source unit cell."""

    source_unit_cell: UnitCell
    repetitions: SuperCellRepetitions

    def __post_init__(self) -> None:
        if not isinstance(self.source_unit_cell, UnitCell):
            raise TypeError("source_unit_cell must be a UnitCell")
        if not (
            type(self.repetitions) is tuple
            and len(self.repetitions) == 3
            and all(type(value) is int for value in self.repetitions)
        ):
            raise TypeError("repetitions must be a three-tuple of built-in ints")
        if any(value < 1 for value in self.repetitions):
            raise ValueError("repetitions values must be positive")
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
        source_atoms = self.supercell.source_unit_cell.atomic_basis.atoms
        for atom, origin in zip(
            self.supercell.atomic_basis.atoms,
            self.supercell.site_origins,
            strict=True,
        ):
            if atom.symbol != source_atoms[origin.source_atom_index].symbol:
                raise ValueError(
                    "constructed pristine supercell must retain source symbols"
                )


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
        for translation in product(
            range(request.repetitions[0]),
            range(request.repetitions[1]),
            range(request.repetitions[2]),
        ):
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
