from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pytest

from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.physkit.periodic.unit_cell import (
    Atom,
    AtomicBasis,
    UnitCell,
    UnitCellJsonCodec,
)
from projectkoios.physkit.units import (
    PhysicalUnit,
    ScalarQuantity,
    Unitless,
    VectorQuantity,
)
from projectkoios.simulations.structure import (
    DerivedStructureProvenance,
    StructureIntegrityError,
    StructureLibrary,
    StructureLibraryEntry,
    StructureLibraryManifestLoader,
    StructureRecord,
    StructureRecordReference,
    StructureRepresentation,
    StructureResolution,
)

BASE_CELL = UnitCell(
    direct_lattice=DirectLattice3D(
        a1=np.array([1.0, 0.0, 0.0]),
        a2=np.array([0.0, 1.0, 0.0]),
        a3=np.array([0.0, 0.0, 1.0]),
    ),
    lattice_parameter=ScalarQuantity(5.43, PhysicalUnit("angstrom")),
    atomic_basis=AtomicBasis(
        atoms=(
            Atom(
                symbol="Si",
                position_fractional=VectorQuantity(
                    np.array((0.0, 0.0, 0.0)),
                    Unitless(),
                ),
            ),
        )
    ),
)


def test_resolves_exact_base_unit_cell(tmp_path: Path) -> None:
    content = (
        UnitCellJsonCodec()
        .dumps(
            BASE_CELL,
            structure_id="Si.DerivedUnitCell",
        )
        .encode()
    )
    sha256 = hashlib.sha256(content).hexdigest()
    parameters_json = '{"diagonal":[2,2,2],"operation":"supercell"}\n'
    (tmp_path / "derived.json").write_bytes(content)
    record = StructureRecord(
        structure_id="Si.DerivedUnitCell",
        representation=StructureRepresentation.unit_cell,
        schema_version=1,
        byte_size=len(content),
        sha256=sha256,
        provenance=DerivedStructureProvenance(
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
            parameters_json=parameters_json,
            parameters_sha256=hashlib.sha256(parameters_json.encode()).hexdigest(),
            result_sha256=sha256,
        ),
    )
    library = StructureLibrary(
        root=tmp_path,
        entries=(StructureLibraryEntry(record, "derived.json"),),
    )

    resolution = library.resolve(record)

    assert type(resolution.unit_cell) is UnitCell
    assert resolution.record.representation is StructureRepresentation.unit_cell


def test_rejects_base_unit_cell_claimed_as_primitive(tmp_path: Path) -> None:
    content = (
        UnitCellJsonCodec()
        .dumps(
            BASE_CELL,
            structure_id="Si.DerivedUnitCell",
        )
        .encode()
    )
    sha256 = hashlib.sha256(content).hexdigest()
    parameters_json = '{"operation":"identity"}\n'
    (tmp_path / "derived.json").write_bytes(content)
    record = StructureRecord(
        structure_id="Si.DerivedUnitCell",
        representation=StructureRepresentation.primitive,
        schema_version=1,
        byte_size=len(content),
        sha256=sha256,
        provenance=DerivedStructureProvenance(
            operation_id="projectkoios.structure.identity",
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
            parameters_json=parameters_json,
            parameters_sha256=hashlib.sha256(parameters_json.encode()).hexdigest(),
            result_sha256=sha256,
        ),
    )
    library = StructureLibrary(
        root=tmp_path,
        entries=(StructureLibraryEntry(record, "derived.json"),),
    )

    with pytest.raises(StructureIntegrityError, match="primitive"):
        library.resolve(record)


def test_rejects_direct_resolution_with_mismatched_exact_cell_type(
    tmp_path: Path,
) -> None:
    content = (
        UnitCellJsonCodec()
        .dumps(BASE_CELL, structure_id="Si.MislabeledPrimitive")
        .encode()
    )
    sha256 = hashlib.sha256(content).hexdigest()
    parameters_json = '{"operation":"identity"}\n'
    record = StructureRecord(
        structure_id="Si.MislabeledPrimitive",
        representation=StructureRepresentation.primitive,
        schema_version=1,
        byte_size=len(content),
        sha256=sha256,
        provenance=DerivedStructureProvenance(
            operation_id="projectkoios.structure.identity",
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
            parameters_json=parameters_json,
            parameters_sha256=hashlib.sha256(parameters_json.encode()).hexdigest(),
            result_sha256=sha256,
        ),
    )

    with pytest.raises(TypeError, match="exact type"):
        StructureResolution(
            record=record,
            path=(tmp_path / "mislabeled.json").resolve(),
            unit_cell=BASE_CELL,
        )


def test_manifest_loads_derived_unit_cell_provenance(tmp_path: Path) -> None:
    content = (
        UnitCellJsonCodec()
        .dumps(
            BASE_CELL,
            structure_id="Si.DerivedUnitCell",
        )
        .encode()
    )
    sha256 = hashlib.sha256(content).hexdigest()
    parameters_json = '{"diagonal":[2,2,2],"operation":"supercell"}\n'
    parameters_sha256 = hashlib.sha256(parameters_json.encode()).hexdigest()
    (tmp_path / "derived.json").write_bytes(content)
    (tmp_path / "catalog.toml").write_text(
        f"""schema_version = 1

[[records]]
structure_id = "Si.DerivedUnitCell"
representation = "unit-cell"
schema_version = 1
sha256 = "{sha256}"
byte_size = {len(content)}
relative_path = "derived.json"

[records.provenance]
kind = "derived"
operation_id = "projectkoios.structure.supercell"
operation_version = "1"
parameters_json = '''{parameters_json}'''
parameters_sha256 = "{parameters_sha256}"
result_sha256 = "{sha256}"

[[records.provenance.parents]]
structure_id = "Si.PrimitiveUnitCell"
representation = "primitive"
schema_version = 1
byte_size = 680
sha256 = "{"1" * 64}"
""",
        encoding="utf-8",
    )

    library = StructureLibraryManifestLoader(
        (tmp_path / "catalog.toml").resolve()
    ).load()

    record = library.require_unique("Si.DerivedUnitCell")
    assert type(record.provenance) is DerivedStructureProvenance
    assert type(library.resolve(record).unit_cell) is UnitCell
