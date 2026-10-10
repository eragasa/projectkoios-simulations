from __future__ import annotations

from projectkoios.integrations.materials_project import (
    MaterialsProjectElementalReferenceRequest,
    MaterialsProjectElementalReferenceSelector,
)
from tests.projectkoios.integrations.materials_project.support import (
    BORON_HIGH,
    BORON_LOW,
    BORON_STRUCTURE,
    MaterialsProjectClientDouble,
)


def test_passes_explicit_query_and_structure_request_to_client() -> None:
    client = MaterialsProjectClientDouble(
        entries={"B": [BORON_HIGH, BORON_LOW]},
        structures={"mp-160": BORON_STRUCTURE, "mp-999": BORON_STRUCTURE},
    )

    MaterialsProjectElementalReferenceSelector().action(
        client=client,
        request=MaterialsProjectElementalReferenceRequest(
            element_symbol="B",
            thermo_types=("GGA_GGA+U_R2SCAN",),
        ),
    )

    assert client.requested_elements == ["B"]
    assert client.requested_criteria == {"thermo_types": ["GGA_GGA+U_R2SCAN"]}
    assert type(client.requested_material_id) is str
    assert client.requested_final is True
    assert client.requested_conventional is False
