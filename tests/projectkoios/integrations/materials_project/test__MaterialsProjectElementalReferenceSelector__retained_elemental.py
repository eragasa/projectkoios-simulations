from __future__ import annotations

import json
from pathlib import Path

from projectkoios.integrations.materials_project import (
    MaterialsProjectCandidateSnapshot,
    MaterialsProjectElementalReference,
    MaterialsProjectElementalReferenceRequest,
    MaterialsProjectQuerySnapshot,
    MaterialsProjectStructureReference,
)
from projectkoios.physkit.periodic.unit_cell import (
    PrimitiveUnitCell,
    UnitCellJsonCodec,
)


def test_rehydrates_retained_ni_query_and_structure_through_owned_contracts() -> None:
    repository = Path(__file__).resolve().parents[4]
    structure_root = repository / "examples/workflows/pw_dft_scf/structures"
    payload = json.loads(
        (structure_root / "provenance/Ni.mp-23.GGA_GGA+U_R2SCAN.json").read_text(
            encoding="utf-8"
        )
    )
    request_payload = payload["request"]
    query_payload = payload["query_snapshot"]
    structure_payload = payload["structure"]
    selection_payload = payload["selection"]
    request = MaterialsProjectElementalReferenceRequest(
        element_symbol=request_payload["element_symbol"],
        thermo_types=tuple(request_payload["thermo_types"]),
        conventional_unit_cell=request_payload["conventional_unit_cell"],
    )
    query = MaterialsProjectQuerySnapshot(
        element_symbol=query_payload["element_symbol"],
        thermo_types=tuple(query_payload["thermo_types"]),
        criteria_json=query_payload["criteria_json"],
        candidates=tuple(
            MaterialsProjectCandidateSnapshot(**candidate)
            for candidate in query_payload["candidates"]
        ),
        source_order_content_identities=tuple(
            tuple(value) for value in query_payload["source_order_content_identities"]
        ),
        response_byte_size=query_payload["response_byte_size"],
        response_sha256=query_payload["response_sha256"],
        client_implementation=query_payload["client_implementation"],
        retrieved_at_utc=query_payload["retrieved_at_utc"],
        mp_api_version=query_payload["mp_api_version"],
        pymatgen_version=query_payload["pymatgen_version"],
        api_endpoint=query_payload["api_endpoint"],
        database_release=query_payload["database_release"],
    )
    unit_cell = UnitCellJsonCodec().loads(
        (structure_root / "Ni.mp-23.PrimitiveUnitCell.json").read_text(
            encoding="utf-8"
        ),
        expected_structure_id=structure_payload["structure_id"],
    )
    structure = MaterialsProjectStructureReference(
        material_id=structure_payload["material_id"],
        source_url=structure_payload["source_url"],
        database_name=structure_payload["database_name"],
        geometry_status=structure_payload["geometry_status"],
        unit_cell=unit_cell,
        structure_id=structure_payload["structure_id"],
        representation=structure_payload["representation"],
        schema_version=structure_payload["schema_version"],
        byte_size=structure_payload["byte_size"],
        sha256=structure_payload["sha256"],
    )
    reference = MaterialsProjectElementalReference(
        request=request,
        material_id=selection_payload["material_id"],
        energy_per_atom_ev=selection_payload["energy_per_atom_ev"],
        energy_above_hull_ev=selection_payload["energy_above_hull_ev"],
        entry_count=selection_payload["entry_count"],
        structure=structure,
        query_snapshot=query,
        selected_candidate_sha256=selection_payload["selected_candidate_sha256"],
    )

    assert type(reference.structure.unit_cell) is PrimitiveUnitCell
    assert reference.structure.material_id == reference.material_id
    assert reference.entry_count == len(reference.query_snapshot.candidates)


def test_rehydrates_retained_b_and_p_queries_and_structures() -> None:
    repository = Path(__file__).resolve().parents[4]
    structure_root = repository / "examples/workflows/pw_dft_scf/structures"
    for element_symbol, material_id in (("B", "mp-160"), ("P", "mp-568348")):
        payload = json.loads(
            (
                structure_root
                / "provenance"
                / f"{element_symbol}.{material_id}.GGA_GGA+U_R2SCAN.json"
            ).read_text(encoding="utf-8")
        )
        request_payload = payload["request"]
        query_payload = payload["query_snapshot"]
        structure_payload = payload["structure"]
        selection_payload = payload["selection"]
        request = MaterialsProjectElementalReferenceRequest(
            element_symbol=request_payload["element_symbol"],
            thermo_types=tuple(request_payload["thermo_types"]),
            conventional_unit_cell=request_payload["conventional_unit_cell"],
        )
        query = MaterialsProjectQuerySnapshot(
            element_symbol=query_payload["element_symbol"],
            thermo_types=tuple(query_payload["thermo_types"]),
            criteria_json=query_payload["criteria_json"],
            candidates=tuple(
                MaterialsProjectCandidateSnapshot(**candidate)
                for candidate in query_payload["candidates"]
            ),
            source_order_content_identities=tuple(
                tuple(value)
                for value in query_payload["source_order_content_identities"]
            ),
            response_byte_size=query_payload["response_byte_size"],
            response_sha256=query_payload["response_sha256"],
            client_implementation=query_payload["client_implementation"],
            retrieved_at_utc=query_payload["retrieved_at_utc"],
            mp_api_version=query_payload["mp_api_version"],
            pymatgen_version=query_payload["pymatgen_version"],
            api_endpoint=query_payload["api_endpoint"],
            database_release=query_payload["database_release"],
        )
        unit_cell = UnitCellJsonCodec().loads(
            (
                structure_root
                / f"{element_symbol}.{material_id}.PrimitiveUnitCell.json"
            ).read_text(encoding="utf-8"),
            expected_structure_id=structure_payload["structure_id"],
        )
        structure = MaterialsProjectStructureReference(
            material_id=structure_payload["material_id"],
            source_url=structure_payload["source_url"],
            database_name=structure_payload["database_name"],
            geometry_status=structure_payload["geometry_status"],
            unit_cell=unit_cell,
            structure_id=structure_payload["structure_id"],
            representation=structure_payload["representation"],
            schema_version=structure_payload["schema_version"],
            byte_size=structure_payload["byte_size"],
            sha256=structure_payload["sha256"],
        )
        reference = MaterialsProjectElementalReference(
            request=request,
            material_id=selection_payload["material_id"],
            energy_per_atom_ev=selection_payload["energy_per_atom_ev"],
            energy_above_hull_ev=selection_payload["energy_above_hull_ev"],
            entry_count=selection_payload["entry_count"],
            structure=structure,
            query_snapshot=query,
            selected_candidate_sha256=selection_payload["selected_candidate_sha256"],
        )

        assert type(reference.structure.unit_cell) is PrimitiveUnitCell
        assert reference.request.element_symbol == element_symbol
        assert reference.material_id == material_id
        assert reference.entry_count == 15
        assert {atom.symbol for atom in unit_cell.atomic_basis.atoms} == {
            element_symbol
        }
