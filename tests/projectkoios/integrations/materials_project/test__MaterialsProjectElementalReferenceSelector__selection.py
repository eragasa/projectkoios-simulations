from __future__ import annotations

import pytest
from pymatgen.core import Structure
from pymatgen.entries.computed_entries import ComputedEntry

from projectkoios.integrations.materials_project import (
    MaterialsProjectElementalReference,
    MaterialsProjectElementalReferenceRequest,
    MaterialsProjectElementalReferenceSelector,
    MaterialsProjectQuerySnapshot,
)
from projectkoios.physkit.periodic.unit_cell import PrimitiveUnitCell
from tests.projectkoios.integrations.materials_project.support import (
    BORON_HIGH,
    BORON_LOW,
    BORON_STRUCTURE,
    PHOSPHORUS_HIGH,
    PHOSPHORUS_LOW,
    PHOSPHORUS_STRUCTURE,
    MaterialsProjectClientDouble,
)


@pytest.mark.parametrize(
    ("symbol", "entries", "structures"),
    (
        (
            "B",
            (BORON_HIGH, BORON_LOW),
            {"mp-160": BORON_STRUCTURE, "mp-999": BORON_STRUCTURE},
        ),
        (
            "P",
            (PHOSPHORUS_HIGH, PHOSPHORUS_LOW),
            {"mp-157": PHOSPHORUS_STRUCTURE, "mp-888": PHOSPHORUS_STRUCTURE},
        ),
    ),
)
def test_selects_typed_elemental_reference(
    symbol: str,
    entries: tuple[ComputedEntry, ...],
    structures: dict[str, Structure],
) -> None:
    client = MaterialsProjectClientDouble(
        entries={symbol: list(entries)},
        structures=structures,
    )

    reference = MaterialsProjectElementalReferenceSelector().action(
        client=client,
        request=MaterialsProjectElementalReferenceRequest(
            element_symbol=symbol,
            thermo_types=("GGA_GGA+U_R2SCAN",),
        ),
    )

    assert type(reference) is MaterialsProjectElementalReference
    assert type(reference.query_snapshot) is MaterialsProjectQuerySnapshot
    assert type(reference.structure.unit_cell) is PrimitiveUnitCell
