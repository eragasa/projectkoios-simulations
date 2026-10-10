# Structure library implementation rules

## Current implementation

`src/python/projectkoios/simulations/structure/library.py` supports exact
version-one primitive, conventional, and base-unit-cell records. It verifies
manifest shape, tagged provenance variants, path containment, regular-file
status, byte size, SHA-256, embedded structure identity, schema version, and
exact decoded PhysKit type.

## General-unit-cell representation

Defect studies use the third representation:

```text
StructureRepresentation.unit_cell = "unit-cell"
```

It stores an exact base PhysKit `UnitCell` without implying that the cell is
primitive, conventional, pristine, ideal, or relaxed. Those scientific meanings
belong to provenance.

The reviewed PhysKit `UnitCellJsonCodec` extension adds the version-one
`unit-cell` discriminator while preserving existing primitive and conventional
bytes. Simulations consumes that codec and does not copy or fork PhysKit's cell
model or serialization logic. Release packaging must require a PhysKit release
that contains this extension before `unit-cell` is advertised outside the
coordinated source worktrees.

The codec preserves deterministic UTF-8 JSON, explicit units,
ordered atoms, fractional positions, lattice-vector orientation, one trailing
newline, strict key sets, finite numeric values, and exact representation-aware
decoding.

## Provenance variants

`StructureRecord.provenance` is a closed union of frozen, slotted records:

- `TransferredStructureProvenance` identifies an immutable source, exact
  revision or retained external snapshot, source path, source digest, and
  separately correlated result digest;
- `DerivedStructureProvenance` identifies exact parent structure references and
  a deterministic derivation such as a supercell transformation or
  `UnitCellDefectDelta`; and
- `ObservedStructureProvenance` identifies the exact starting structure,
  relaxation calculation, qualifying relaxation evidence, relaxation scope, and
  publication operation through immutable content references.

To avoid a cycle in which simulation records reference structures while
structure records import simulation packages, observed provenance uses local
semantic references containing the owning record's stable ID, representation,
schema version, byte size, and SHA-256. A publication action must validate those
references against caller-supplied complete simulation and evidence records;
the structure package imports neither owning package.

Every variant records the digest of the resulting structure bytes separately
from parent/source digests. A derived or observed record must not pretend its
output bytes were transferred unchanged from a parent.

## Derivation payloads

A pristine supercell derivation records the complete parent `StructureRecord`
and integer transformation. The first implementation supports the existing
positive diagonal replication semantics; a later general transformation uses a
full nonsingular integer matrix.

An ideal defect derivation records:

- exact pristine host-supercell record;
- original-index removals;
- ordered additions with species and fractional positions;
- `charge_state`; and
- the invariant that lattice and retained host positions are unchanged.

An observed relaxation derivation records the starting structure, exact
relaxation specification, evidence record, and scope. It must not infer a
relaxed record directly from an ideal delta.

## Manifest and resolution

The manifest continues to bind one complete record to one normalized relative
path. Resolution verifies bytes before decoding, then requires the exact decoded
type declared by the representation:

- `primitive` -> exact `PrimitiveUnitCell`;
- `conventional` -> exact `ConventionalUnitCell`;
- `unit-cell` -> exact base `UnitCell`.

Stable-ID ambiguity remains fail-closed. A complete record, including provenance
variant and content digest, is required for exact selection.

## Atomic migration status

The enum, manifest loader, public exports, reviewed catalog, tests, and
architecture documentation use the new records. The old transfer-only
`StructureProvenance` no longer exists and no alias or compatibility facade is
provided. Pure DFT relaxed-structure publication is implemented in the DFT
relaxation package; catalog/file persistence and installed-wheel verification
remain pending, as does selection of the released PhysKit minimum version.

## Required verification

Tests must cover all representations and provenance variants, deterministic
round trips, parent and evidence correlation, changed parent records, lattice
and position invariants, ordered atoms, schema rejection, byte and digest
mismatch, path escape, symlinks, ambiguity, and installed-wheel resolution. No
test executes a calculator.
