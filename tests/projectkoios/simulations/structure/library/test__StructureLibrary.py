from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.physkit.periodic.unit_cell import (
    Atom,
    AtomicBasis,
    ConventionalUnitCell,
    PrimitiveUnitCell,
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
    StructureConflictError,
    StructureIntegrityError,
    StructureLibrary,
    StructureLibraryEntry,
    StructureLibraryManifestLoader,
    StructureManifestError,
    StructureNotFoundError,
    StructureRecord,
    StructureRepresentation,
    TransferredStructureProvenance,
)

PRIMITIVE_CELL = PrimitiveUnitCell(
    direct_lattice=DirectLattice3D(
        a1=np.array([0.5, 0.5, 0.0]),
        a2=np.array([0.5, 0.0, 0.5]),
        a3=np.array([0.0, 0.5, 0.5]),
    ),
    lattice_parameter=ScalarQuantity(5.43, PhysicalUnit("angstrom")),
    atomic_basis=AtomicBasis(
        atoms=(
            Atom(
                symbol="Si",
                position_fractional=VectorQuantity(
                    magnitude=np.asarray((0.0, 0.0, 0.0)),
                    unit=Unitless(),
                ),
            ),
            Atom(
                symbol="Si",
                position_fractional=VectorQuantity(
                    magnitude=np.asarray((0.25, 0.25, 0.25)),
                    unit=Unitless(),
                ),
            ),
        )
    ),
)
PRIMITIVE_CELL_544 = PrimitiveUnitCell(
    direct_lattice=PRIMITIVE_CELL.direct_lattice,
    lattice_parameter=ScalarQuantity(5.44, PhysicalUnit("angstrom")),
    atomic_basis=PRIMITIVE_CELL.atomic_basis,
)
CONVENTIONAL_CELL = ConventionalUnitCell(
    direct_lattice=DirectLattice3D(
        a1=np.array([1.0, 0.0, 0.0]),
        a2=np.array([0.0, 1.0, 0.0]),
        a3=np.array([0.0, 0.0, 1.0]),
    ),
    lattice_parameter=ScalarQuantity(5.43, PhysicalUnit("angstrom")),
    atomic_basis=PRIMITIVE_CELL.atomic_basis,
)


class StructureLibraryTest(unittest.TestCase):
    def test_loads_and_resolves_the_reviewed_structure_catalog(self) -> None:
        repository = Path(__file__).resolve().parents[5]
        manifest = repository / "examples/workflows/pw_dft_scf/structures/catalog.toml"

        library = StructureLibraryManifestLoader(manifest.resolve()).load()

        self.assertEqual(
            tuple(record.structure_id for record in library.records()),
            (
                "Si.PrimitiveUnitCell",
                "Si.ConventionalUnitCell",
                "materials-project.mp-23.primitive",
                "materials-project.mp-160.primitive",
                "materials-project.mp-568348.primitive",
                "Si.Supercell.Atoms64",
                "Si.P.Substitutional.Atoms64.Ideal",
                "Si.B.Substitutional.Atoms64.Ideal",
                "Si.Supercell.Atoms216",
                "Si.P.Substitutional.Atoms216.Ideal",
                "Si.B.Substitutional.Atoms216.Ideal",
                "Si.Supercell.Atoms512",
                "Si.P.Substitutional.Atoms512.Ideal",
                "Si.B.Substitutional.Atoms512.Ideal",
            ),
        )
        primitive = library.resolve_unique("Si.PrimitiveUnitCell")
        conventional = library.resolve_unique("Si.ConventionalUnitCell")
        nickel = library.resolve_unique("materials-project.mp-23.primitive")
        boron = library.resolve_unique("materials-project.mp-160.primitive")
        phosphorus = library.resolve_unique("materials-project.mp-568348.primitive")
        self.assertIs(type(primitive.unit_cell), PrimitiveUnitCell)
        self.assertIs(type(conventional.unit_cell), ConventionalUnitCell)
        self.assertEqual(
            primitive.record.representation,
            StructureRepresentation.primitive,
        )
        self.assertEqual(
            conventional.record.representation,
            StructureRepresentation.conventional,
        )
        self.assertIs(type(nickel.unit_cell), PrimitiveUnitCell)
        self.assertEqual(
            tuple(atom.symbol for atom in nickel.unit_cell.atomic_basis.atoms),
            ("Ni",),
        )
        self.assertEqual(
            {atom.symbol for atom in boron.unit_cell.atomic_basis.atoms},
            {"B"},
        )
        self.assertEqual(
            {atom.symbol for atom in phosphorus.unit_cell.atomic_basis.atoms},
            {"P"},
        )
        for external, material_id in (
            (nickel, "mp-23"),
            (boron, "mp-160"),
            (phosphorus, "mp-568348"),
        ):
            self.assertEqual(
                external.record.provenance.source,
                "https://api.materialsproject.org/",
            )
            provenance_path = repository / external.record.provenance.record_path
            provenance_content = provenance_path.read_bytes()
            self.assertEqual(
                hashlib.sha256(provenance_content).hexdigest(),
                external.record.provenance.source_sha256,
            )
            provenance_payload = json.loads(provenance_content)
            self.assertEqual(
                provenance_payload["selection"]["material_id"], material_id
            )
            self.assertEqual(
                provenance_payload["structure"]["sha256"],
                external.record.sha256,
            )
            self.assertEqual(
                sum(
                    candidate["material_id"] == material_id
                    and candidate["sha256"]
                    == provenance_payload["selection"]["selected_candidate_sha256"]
                    for candidate in provenance_payload["query_snapshot"]["candidates"]
                ),
                1,
            )
            self.assertNotIn("MP_API_KEY", provenance_content.decode("utf-8"))
        derived = []
        for atom_count in (64, 216, 512):
            bulk = library.resolve_unique(f"Si.Supercell.Atoms{atom_count}")
            phosphorus_defect = library.resolve_unique(
                f"Si.P.Substitutional.Atoms{atom_count}.Ideal"
            )
            boron_defect = library.resolve_unique(
                f"Si.B.Substitutional.Atoms{atom_count}.Ideal"
            )
            self.assertIs(type(bulk.unit_cell), UnitCell)
            self.assertEqual(len(bulk.unit_cell.atomic_basis.atoms), atom_count)
            self.assertEqual(
                len(phosphorus_defect.unit_cell.atomic_basis.atoms), atom_count
            )
            self.assertEqual(len(boron_defect.unit_cell.atomic_basis.atoms), atom_count)
            self.assertEqual(
                phosphorus_defect.unit_cell.atomic_basis.atoms[-1].symbol, "P"
            )
            self.assertEqual(boron_defect.unit_cell.atomic_basis.atoms[-1].symbol, "B")
            self.assertIs(type(bulk.record.provenance), DerivedStructureProvenance)
            self.assertEqual(
                bulk.record.provenance.parents[0].sha256,
                conventional.record.sha256,
            )
            for defect in (phosphorus_defect, boron_defect):
                self.assertIs(
                    type(defect.record.provenance), DerivedStructureProvenance
                )
                self.assertEqual(
                    defect.record.provenance.parents[0].sha256,
                    bulk.record.sha256,
                )
            derived.extend((bulk, phosphorus_defect, boron_defect))
        for resolution in (
            primitive,
            conventional,
            nickel,
            boron,
            phosphorus,
            *derived,
        ):
            content = resolution.path.read_bytes()
            self.assertEqual(len(content), resolution.record.byte_size)
            self.assertEqual(
                hashlib.sha256(content).hexdigest(),
                resolution.record.sha256,
            )
            self.assertEqual(
                resolution.record.sha256,
                resolution.record.provenance.result_sha256,
            )

    def test_resolves_one_exact_declared_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            content = (
                UnitCellJsonCodec()
                .dumps(
                    PRIMITIVE_CELL,
                    structure_id="Si.Primitive",
                )
                .encode()
            )
            (root / "primitive.json").write_bytes(content)
            sha256 = hashlib.sha256(content).hexdigest()
            record = StructureRecord(
                structure_id="Si.Primitive",
                representation=StructureRepresentation.primitive,
                schema_version=1,
                sha256=sha256,
                byte_size=len(content),
                provenance=TransferredStructureProvenance(
                    source="https://example.invalid/structures",
                    revision="revision-1",
                    record_path="source/primitive.json",
                    source_sha256=sha256,
                    result_sha256=sha256,
                ),
            )
            library = StructureLibrary(
                root=root,
                entries=(
                    StructureLibraryEntry(
                        record=record,
                        relative_path="primitive.json",
                    ),
                ),
            )

            resolution = library.resolve(record)

            self.assertIs(resolution.record, record)
            self.assertEqual(resolution.path, (root / "primitive.json").resolve())
            self.assertIs(type(resolution.unit_cell), PrimitiveUnitCell)
            self.assertEqual(library.require_unique("Si.Primitive"), record)

    def test_requires_explicit_record_selection_when_an_id_has_history(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first_content = (
                UnitCellJsonCodec()
                .dumps(
                    PRIMITIVE_CELL,
                    structure_id="Si.Primitive",
                )
                .encode()
            )
            second_content = (
                UnitCellJsonCodec()
                .dumps(
                    PRIMITIVE_CELL_544,
                    structure_id="Si.Primitive",
                )
                .encode()
            )
            (root / "first.json").write_bytes(first_content)
            (root / "second.json").write_bytes(second_content)
            first_sha256 = hashlib.sha256(first_content).hexdigest()
            second_sha256 = hashlib.sha256(second_content).hexdigest()
            first = StructureRecord(
                structure_id="Si.Primitive",
                representation=StructureRepresentation.primitive,
                schema_version=1,
                sha256=first_sha256,
                byte_size=len(first_content),
                provenance=TransferredStructureProvenance(
                    source="https://example.invalid/structures",
                    revision="revision-1",
                    record_path="source/first.json",
                    source_sha256=first_sha256,
                    result_sha256=first_sha256,
                ),
            )
            second = StructureRecord(
                structure_id="Si.Primitive",
                representation=StructureRepresentation.primitive,
                schema_version=1,
                sha256=second_sha256,
                byte_size=len(second_content),
                provenance=TransferredStructureProvenance(
                    source="https://example.invalid/structures",
                    revision="revision-2",
                    record_path="source/second.json",
                    source_sha256=second_sha256,
                    result_sha256=second_sha256,
                ),
            )
            library = StructureLibrary(
                root=root,
                entries=(
                    StructureLibraryEntry(first, "first.json"),
                    StructureLibraryEntry(second, "second.json"),
                ),
            )

            self.assertEqual(library.records("Si.Primitive"), (first, second))
            self.assertIs(library.resolve(first).record, first)
            self.assertIs(library.resolve(second).record, second)
            with self.assertRaisesRegex(StructureConflictError, "multiple exact"):
                library.require_unique("Si.Primitive")

    def test_reports_missing_and_changed_exact_records(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            content = (
                UnitCellJsonCodec()
                .dumps(
                    CONVENTIONAL_CELL,
                    structure_id="Si.Conventional",
                )
                .encode()
            )
            (root / "cell.json").write_bytes(content)
            sha256 = hashlib.sha256(content).hexdigest()
            record = StructureRecord(
                structure_id="Si.Conventional",
                representation=StructureRepresentation.conventional,
                schema_version=1,
                sha256=sha256,
                byte_size=len(content),
                provenance=TransferredStructureProvenance(
                    source="https://example.invalid/structures",
                    revision="revision-1",
                    record_path="source/cell.json",
                    source_sha256=sha256,
                    result_sha256=sha256,
                ),
            )
            entry = StructureLibraryEntry(record, "cell.json")
            library = StructureLibrary(root=root, entries=(entry,))

            with self.assertRaisesRegex(StructureNotFoundError, "not declared"):
                library.resolve(replace(record, structure_id="Si.Other"))
            with self.assertRaisesRegex(StructureNotFoundError, "not declared"):
                library.require_unique("Si.Other")

            (root / "cell.json").write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(StructureIntegrityError, "byte-size"):
                library.resolve(record)

            (root / "cell.json").unlink()
            with self.assertRaisesRegex(StructureNotFoundError, "unavailable"):
                library.resolve(record)

    def test_rejects_symlinks_and_same_size_content_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            content = (
                UnitCellJsonCodec()
                .dumps(
                    PRIMITIVE_CELL,
                    structure_id="Si.Primitive",
                )
                .encode()
            )
            sha256 = hashlib.sha256(content).hexdigest()
            record = StructureRecord(
                structure_id="Si.Primitive",
                representation=StructureRepresentation.primitive,
                schema_version=1,
                sha256=sha256,
                byte_size=len(content),
                provenance=TransferredStructureProvenance(
                    source="https://example.invalid/structures",
                    revision="revision-1",
                    record_path="source/cell.json",
                    source_sha256=sha256,
                    result_sha256=sha256,
                ),
            )
            target = root / "target.json"
            target.write_bytes(content)
            path = root / "cell.json"
            path.symlink_to(target)
            library = StructureLibrary(
                root=root,
                entries=(StructureLibraryEntry(record, "cell.json"),),
            )

            with self.assertRaisesRegex(StructureNotFoundError, "unavailable"):
                library.resolve(record)

            path.unlink()
            changed = bytearray(content)
            changed[-2] = ord(" ")
            path.write_bytes(changed)
            with self.assertRaisesRegex(StructureIntegrityError, "SHA-256"):
                library.resolve(record)

    def test_rejects_an_embedded_identity_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            content = (
                UnitCellJsonCodec()
                .dumps(
                    PRIMITIVE_CELL,
                    structure_id="Si.Other",
                )
                .encode()
            )
            (root / "cell.json").write_bytes(content)
            sha256 = hashlib.sha256(content).hexdigest()
            record = StructureRecord(
                structure_id="Si.Primitive",
                representation=StructureRepresentation.primitive,
                schema_version=1,
                sha256=sha256,
                byte_size=len(content),
                provenance=TransferredStructureProvenance(
                    source="https://example.invalid/structures",
                    revision="revision-1",
                    record_path="source/cell.json",
                    source_sha256=sha256,
                    result_sha256=sha256,
                ),
            )
            library = StructureLibrary(
                root=root,
                entries=(StructureLibraryEntry(record, "cell.json"),),
            )

            with self.assertRaisesRegex(
                StructureIntegrityError,
                "schema validation",
            ):
                library.resolve(record)

    def test_rejects_a_representation_mismatch_after_byte_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            content = (
                UnitCellJsonCodec()
                .dumps(
                    PRIMITIVE_CELL,
                    structure_id="Si.Cell",
                )
                .encode()
            )
            (root / "cell.json").write_bytes(content)
            sha256 = hashlib.sha256(content).hexdigest()
            primitive = StructureRecord(
                structure_id="Si.Cell",
                representation=StructureRepresentation.primitive,
                schema_version=1,
                sha256=sha256,
                byte_size=len(content),
                provenance=TransferredStructureProvenance(
                    source="https://example.invalid/structures",
                    revision="revision-1",
                    record_path="source/cell.json",
                    source_sha256=sha256,
                    result_sha256=sha256,
                ),
            )
            conventional_claim = replace(
                primitive,
                representation=StructureRepresentation.conventional,
            )
            library = StructureLibrary(
                root=root,
                entries=(StructureLibraryEntry(conventional_claim, "cell.json"),),
            )

            with self.assertRaisesRegex(
                StructureIntegrityError,
                "representation does not match",
            ):
                library.resolve(conventional_claim)

    def test_rejects_conflicting_library_declarations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            content = (
                UnitCellJsonCodec()
                .dumps(
                    PRIMITIVE_CELL,
                    structure_id="Si.Primitive",
                )
                .encode()
            )
            (root / "cell.json").write_bytes(content)
            sha256 = hashlib.sha256(content).hexdigest()
            record = StructureRecord(
                structure_id="Si.Primitive",
                representation=StructureRepresentation.primitive,
                schema_version=1,
                sha256=sha256,
                byte_size=len(content),
                provenance=TransferredStructureProvenance(
                    source="https://example.invalid/structures",
                    revision="revision-1",
                    record_path="source/cell.json",
                    source_sha256=sha256,
                    result_sha256=sha256,
                ),
            )
            entry = StructureLibraryEntry(record, "cell.json")

            with self.assertRaisesRegex(ValueError, "record identities"):
                StructureLibrary(root=root, entries=(entry, entry))
            other_record = replace(
                record,
                structure_id="Si.Other",
                provenance=replace(
                    record.provenance,
                    record_path="source/other.json",
                ),
            )
            with self.assertRaisesRegex(ValueError, "relative paths"):
                StructureLibrary(
                    root=root,
                    entries=(entry, StructureLibraryEntry(other_record, "cell.json")),
                )
            with self.assertRaisesRegex(ValueError, "provenances"):
                StructureLibrary(
                    root=root,
                    entries=(
                        entry,
                        StructureLibraryEntry(
                            replace(record, structure_id="Si.Other"),
                            "other.json",
                        ),
                    ),
                )

    def test_manifest_loader_rejects_unknown_and_unbounded_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            manifest = root / "catalog.toml"
            manifest.write_text(
                "schema_version = 1\nunknown = true\nrecords = []\n",
                encoding="utf-8",
            )
            loader = StructureLibraryManifestLoader(manifest.resolve())

            with self.assertRaisesRegex(StructureManifestError, "keys are invalid"):
                loader.load()
            with self.assertRaisesRegex(StructureManifestError, "byte limit"):
                StructureLibraryManifestLoader(
                    manifest.resolve(),
                    maximum_manifest_bytes=1,
                ).load()


if __name__ == "__main__":
    unittest.main()
