from __future__ import annotations

import pytest
from pymatgen.core import Element, Structure
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


def test_uses_material_identity_from_suffixed_thermo_entry_metadata() -> None:
    lower = ComputedEntry(
        "Ni",
        -6.0,
        entry_id="mp-23-r2SCAN",
        data={
            "material_id": "mp-23",
            "oxidation_states": {Element("Ni"): 0.0},
        },
    )
    higher = ComputedEntry(
        "Ni",
        -5.0,
        entry_id="mp-10257-r2SCAN",
        data={
            "material_id": "mp-10257",
            "oxidation_states": {Element("Ni"): 0.0},
        },
    )
    structure = Structure(
        lattice=[[0.0, 1.75, 1.75], [1.75, 0.0, 1.75], [1.75, 1.75, 0.0]],
        species=("Ni",),
        coords=((0.0, 0.0, 0.0),),
    )
    client = MaterialsProjectClientDouble(
        entries={"Ni": [higher, lower]},
        structures={"mp-23": structure, "mp-10257": structure},
    )

    reference = MaterialsProjectElementalReferenceSelector().action(
        client=client,
        request=MaterialsProjectElementalReferenceRequest(
            element_symbol="Ni",
            thermo_types=("GGA_GGA+U_R2SCAN",),
        ),
    )

    assert reference.material_id == "mp-23"
    assert reference.structure.material_id == "mp-23"
    assert client.requested_material_id == "mp-23"
    assert Element("Ni") in lower.data["oxidation_states"]
    assert {
        candidate.material_id for candidate in reference.query_snapshot.candidates
    } == {
        "mp-23",
        "mp-10257",
    }
