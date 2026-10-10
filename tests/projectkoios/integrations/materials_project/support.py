from __future__ import annotations

from dataclasses import dataclass

from pymatgen.core import Lattice, Structure
from pymatgen.entries.computed_entries import ComputedEntry

BORON_LOW = ComputedEntry("B", -6.0, entry_id="mp-160")
BORON_HIGH = ComputedEntry("B", -5.0, entry_id="mp-999")
PHOSPHORUS_LOW = ComputedEntry("P", -5.0, entry_id="mp-157")
PHOSPHORUS_HIGH = ComputedEntry("P", -4.0, entry_id="mp-888")
BORON_STRUCTURE = Structure(
    Lattice.rhombohedral(5.0, 58.0),
    ("B",),
    ((0.0, 0.0, 0.0),),
)
PHOSPHORUS_STRUCTURE = Structure(
    Lattice.orthorhombic(3.3, 4.4, 10.5),
    ("P",),
    ((0.0, 0.0, 0.0),),
)


@dataclass(slots=True)
class MaterialsProjectClientDouble:
    entries: dict[str, list[ComputedEntry]]
    structures: dict[str, Structure]
    requested_elements: list[str] | None = None
    requested_criteria: dict[str, list[str]] | None = None
    requested_material_id: str | None = None
    requested_final: bool | None = None
    requested_conventional: bool | None = None

    def get_entries_in_chemsys(
        self,
        elements: list[str],
        additional_criteria: dict[str, list[str]],
    ) -> list[ComputedEntry]:
        self.requested_elements = elements
        self.requested_criteria = additional_criteria
        return self.entries[elements[0]]

    def get_structure_by_material_id(
        self,
        material_id: str,
        final: bool = True,
        conventional_unit_cell: bool = False,
    ) -> Structure | list[Structure]:
        self.requested_material_id = material_id
        self.requested_final = final
        self.requested_conventional = conventional_unit_cell
        return self.structures[material_id]
