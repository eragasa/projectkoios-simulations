# Exact manifest-backed structure library

## Contract

`StructureLibrary` resolves immutable structure records declared by a strict
TOML manifest. A `StructureRecord` carries:

- a stable qualified `structure_id`;
- a `primitive`, `conventional`, or `unit-cell` `StructureRepresentation`;
- unit-cell JSON schema version `1`;
- exact byte size and lowercase SHA-256;
- one closed provenance variant: `TransferredStructureProvenance`,
  `DerivedStructureProvenance`, or `ObservedStructureProvenance`.

`StructureLibraryEntry` binds that record to one normalized relative `.json`
path below a single explicit root. `StructureResolution` returns the selected
record, verified real path, and decoded PhysKit unit cell.

A stable identifier is not itself a complete exact identity. A library may
retain multiple historical records with the same identifier. In that case,
`require_unique()` and `resolve_unique()` fail with `StructureConflictError`;
the caller must select a complete `StructureRecord`.

## Manifest and resolution

`StructureLibraryManifestLoader` accepts an absolute, regular, nonsymlink TOML
file. It enforces schema version `1`, exact manifest and record key sets,
nonempty records, bounded manifest and record sizes, unique record identities,
unique destination paths, and unique complete provenance values.

Resolution proceeds in this order:

1. match the complete required `StructureRecord`;
2. reject missing files, symlinks, and paths outside the library root;
3. enforce the byte limit and exact declared byte size;
4. verify SHA-256;
5. decode UTF-8 with `UnitCellJsonCodec` using the expected structure ID;
6. require exact decoded type `PrimitiveUnitCell`, `ConventionalUnitCell`, or
   base `UnitCell` according to the declared representation.

The operation never searches by chemical formula, chooses among candidates, or
substitutes bytes. `StructureNotFoundError` reports absence,
`StructureConflictError` reports identifier ambiguity,
`StructureIntegrityError` reports byte/schema/representation failures, and
`StructureManifestError` reports invalid manifests.

## Reviewed silicon records

[`examples/workflows/pw_dft_scf/structures/catalog.toml`](../../../../../../examples/workflows/pw_dft_scf/structures/catalog.toml)
declares the reviewed silicon primitive and conventional cells transferred from
`projectkoios-applications` revision
`416be52d539bfbffdbc8a27bd8e13de65404821b`:

| Structure ID | Representation | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `Si.PrimitiveUnitCell` | primitive | 680 | `6e048c7001f329459e85f321e7bd406f4dd871d6fabf8d12fa349a1623f87ccc` |
| `Si.ConventionalUnitCell` | conventional | 1367 | `e34066dbfcbdc187014256731774a4115674a1f1b6286da5729ad4298b0f4f5e` |

Each manifest entry preserves the historical path, byte size, and SHA-256.
Provenance proves transfer identity; it does not prove numerical correctness or
scientific validation.

## Derived and observed cells

The version-one schema persists exact base `UnitCell` values without relabeling
them as primitive or conventional. One representation-level `unit-cell`
encoding covers three scientific stages; stage meaning belongs to immutable
provenance rather than the serialization representation:

1. an **ideal host-geometry defect** copies the exact host-supercell lattice and
   fractional positions and changes only the species/removal/addition declared
   by `UnitCellDefectDelta`;
2. an **ion-relaxed defect** comes from an
   `ATOMIC_POSITIONS` relaxation, preserves the stage-one lattice, and changes
   atomic positions only; and
3. a **fully relaxed defect** comes from an
   `ATOMIC_POSITIONS_AND_CELL` relaxation and may change both atomic positions
   and lattice parameters under declared pressure controls.

Derived-cell provenance retains exact parent structure references, the stable
operation identity and version, and canonical derivation-parameter bytes plus
their SHA-256. Observed-cell provenance retains the exact starting structure,
relaxation-calculation and evidence references, relaxation scope, publication
operation and version, and result digest. Publishing the project’s concrete
relaxed Si:P and Si:B records remains pending; the library contract does not
infer them from ideal cells.

Library resolution is data access only. It does not discover, authorize, or run
a calculator.

See [`implementation.md`](implementation.md) for the codec and provenance
migration, [`schematics.md`](schematics.md) for derivation and publication
flows, [`scientific.md`](scientific.md) for structure-role qualifications, and
[`numeric.md`](numeric.md) for exact-byte and tolerance boundaries.
