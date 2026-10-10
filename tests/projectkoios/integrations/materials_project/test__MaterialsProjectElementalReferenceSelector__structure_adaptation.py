from __future__ import annotations

import numpy as np
import pytest
from pymatgen.core import Lattice, Structure

from projectkoios.integrations.materials_project import (
    MaterialsProjectStructureRequest,
    MaterialsProjectStructureRetriever,
)
from projectkoios.physkit.periodic.unit_cell import ConventionalUnitCell
from tests.projectkoios.integrations.materials_project.support import (
    MaterialsProjectClientDouble,
)


def test_copies_structure_without_retaining_mutable_pymatgen_arrays() -> None:
    source = Structure(
        Lattice.cubic(5.43),
        ("Si", "Si"),
        ((0.0, 0.0, 0.0), (0.25, 0.25, 0.25)),
    )
    client = MaterialsProjectClientDouble(entries={}, structures={"mp-149": source})

    reference = MaterialsProjectStructureRetriever().action(
        client=client,
        request=MaterialsProjectStructureRequest(
            material_id="mp-149",
            conventional_unit_cell=True,
        ),
    )
    source.translate_sites((0,), (0.1, 0.0, 0.0), frac_coords=True)

    assert type(reference.unit_cell) is ConventionalUnitCell
    np.testing.assert_array_equal(
        reference.unit_cell.atomic_basis.atoms[0].position_fractional.magnitude,
        np.asarray((0.0, 0.0, 0.0)),
    )
    np.testing.assert_array_equal(
        reference.unit_cell.a1.magnitude,
        np.asarray((5.43, 0.0, 0.0)),
    )
    assert reference.geometry_status == "external_reference_not_calculation_input"


def test_rejects_disordered_materials_project_sites() -> None:
    source = Structure(
        Lattice.cubic(5.43),
        ({"Si": 0.5, "Ge": 0.5},),
        ((0.0, 0.0, 0.0),),
    )
    client = MaterialsProjectClientDouble(entries={}, structures={"mp-149": source})

    with pytest.raises(ValueError, match="disordered"):
        MaterialsProjectStructureRetriever().action(
            client=client,
            request=MaterialsProjectStructureRequest("mp-149"),
        )
