from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from projectkoios.simulations.structure import (
    DerivedStructureProvenance,
    ObservedStructureProvenance,
    ObservedStructureScope,
    StructureLibraryManifestLoader,
    StructureProvenanceReference,
    StructureRecord,
    StructureRecordReference,
    StructureRepresentation,
    TransferredStructureProvenance,
)


def test_transferred_provenance_distinguishes_source_and_result_digests() -> None:
    provenance = TransferredStructureProvenance(
        source="https://example.invalid/structure",
        revision="snapshot-1",
        record_path="source/cell.json",
        source_sha256="1" * 64,
        result_sha256="2" * 64,
    )

    assert provenance.source_sha256 != provenance.result_sha256


def test_observed_provenance_correlates_start_calculation_and_evidence() -> None:
    provenance = ObservedStructureProvenance(
        starting_structure=StructureRecordReference(
            structure_id="SiP.IdealUnitCell",
            representation=StructureRepresentation.unit_cell,
            schema_version=1,
            byte_size=100,
            sha256="1" * 64,
        ),
        relaxation_calculation=StructureProvenanceReference(
            stable_id="sip-ion-relaxation",
            representation="projectkoios.pw-dft-relaxation+json",
            schema_version=1,
            byte_size=200,
            sha256="2" * 64,
        ),
        relaxation_evidence=StructureProvenanceReference(
            stable_id="sip-ion-relaxation-evidence",
            representation="projectkoios.simulation-evidence+json",
            schema_version=1,
            byte_size=300,
            sha256="3" * 64,
        ),
        scope=ObservedStructureScope.atomic_positions,
        publication_operation="projectkoios.structure.publish-relaxation",
        publication_version="1",
        result_sha256="4" * 64,
    )

    assert provenance.scope is ObservedStructureScope.atomic_positions


def test_manifest_loads_observed_provenance(tmp_path: Path) -> None:
    manifest = tmp_path / "catalog.toml"
    manifest.write_text(
        f'''schema_version = 1

[[records]]
structure_id = "SiP.IonRelaxedUnitCell"
representation = "unit-cell"
schema_version = 1
sha256 = "{"4" * 64}"
byte_size = 100
relative_path = "observed.json"

[records.provenance]
kind = "observed"
scope = "atomic-positions"
publication_operation = "projectkoios.structure.publish-relaxation"
publication_version = "1"
result_sha256 = "{"4" * 64}"

[records.provenance.starting_structure]
structure_id = "SiP.IdealUnitCell"
representation = "unit-cell"
schema_version = 1
byte_size = 100
sha256 = "{"1" * 64}"

[records.provenance.relaxation_calculation]
stable_id = "sip-ion-relaxation"
representation = "projectkoios.pw-dft-relaxation+json"
schema_version = 1
byte_size = 200
sha256 = "{"2" * 64}"

[records.provenance.relaxation_evidence]
stable_id = "sip-ion-relaxation-evidence"
representation = "projectkoios.simulation-evidence+json"
schema_version = 1
byte_size = 300
sha256 = "{"3" * 64}"
''',
        encoding="utf-8",
    )

    library = StructureLibraryManifestLoader(manifest.resolve()).load()

    record = library.require_unique("SiP.IonRelaxedUnitCell")
    assert type(record.provenance) is ObservedStructureProvenance


def test_rejects_noncanonical_derived_parameters() -> None:
    with pytest.raises(ValueError, match="canonical JSON"):
        DerivedStructureProvenance(
            operation_id="projectkoios.structure.supercell",
            operation_version="1",
            parents=(
                StructureRecordReference(
                    structure_id="Si.PrimitiveUnitCell",
                    representation=StructureRepresentation.primitive,
                    schema_version=1,
                    byte_size=680,
                    sha256="1" * 64,
                ),
            ),
            parameters_json='{ "diagonal": [2, 2, 2] }',
            parameters_sha256=hashlib.sha256(b'{ "diagonal": [2, 2, 2] }').hexdigest(),
            result_sha256="2" * 64,
        )


def test_rejects_nonfinite_derived_parameters() -> None:
    with pytest.raises(ValueError, match="finite"):
        DerivedStructureProvenance(
            operation_id="projectkoios.structure.supercell",
            operation_version="1",
            parents=(
                StructureRecordReference(
                    structure_id="Si.PrimitiveUnitCell",
                    representation=StructureRepresentation.primitive,
                    schema_version=1,
                    byte_size=680,
                    sha256="1" * 64,
                ),
            ),
            parameters_json='{"value":NaN}\n',
            parameters_sha256="2" * 64,
            result_sha256="3" * 64,
        )


def test_rejects_record_and_provenance_result_digest_mismatch() -> None:
    with pytest.raises(ValueError, match="provenance result SHA-256"):
        StructureRecord(
            structure_id="Si.TransferredUnitCell",
            representation=StructureRepresentation.unit_cell,
            schema_version=1,
            byte_size=100,
            sha256="1" * 64,
            provenance=TransferredStructureProvenance(
                source="https://example.invalid/structure",
                revision="snapshot-1",
                record_path="source/cell.json",
                source_sha256="1" * 64,
                result_sha256="2" * 64,
            ),
        )


def test_rejects_an_untyped_observed_scope() -> None:
    with pytest.raises(TypeError, match="ObservedStructureScope"):
        ObservedStructureProvenance(
            starting_structure=StructureRecordReference(
                structure_id="SiP.IdealUnitCell",
                representation=StructureRepresentation.unit_cell,
                schema_version=1,
                byte_size=100,
                sha256="1" * 64,
            ),
            relaxation_calculation=StructureProvenanceReference(
                stable_id="sip-ion-relaxation",
                representation="projectkoios.pw-dft-relaxation+json",
                schema_version=1,
                byte_size=200,
                sha256="2" * 64,
            ),
            relaxation_evidence=StructureProvenanceReference(
                stable_id="sip-ion-relaxation-evidence",
                representation="projectkoios.simulation-evidence+json",
                schema_version=1,
                byte_size=300,
                sha256="3" * 64,
            ),
            scope="atomic-positions",  # type: ignore[arg-type]
            publication_operation="projectkoios.structure.publish-relaxation",
            publication_version="1",
            result_sha256="4" * 64,
        )
