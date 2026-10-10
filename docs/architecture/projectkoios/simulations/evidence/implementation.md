# Simulation evidence implementation rules

## Current and planned production modules

```text
src/python/projectkoios/simulations/evidence/
  __init__.py    # current
  artifact.py    # current exact artifact references
  record.py      # current correlation, normalization, and canonical identity bytes
  codec.py       # planned strict decoding
  library.py     # planned storage-independent resolution
```

The current package provides exact evidence records. Existing SCF observations
and artifact contracts remain in their domain modules and are referenced rather
than duplicated. The protected relaxation domain now has neutral observation
and result contracts; outward QE and VASP normalization adapters remain
prerequisites for calculator evidence.

## Record boundary

The initial `SimulationEvidenceRecord` binds:

- its own stable evidence ID and schema version;
- evaluation and task correlation identities supplied by the owning runtime;
- one exact local simulation content reference;
- the SHA-256 of one exact `CalculatorInputRecord`;
- one calculator integration identity and observed provider version;
- an exact mechanical execution-record artifact;
- exact native artifact records; and
- exact normalization operation and normalized-output content identity.

The record emits deterministic canonical whole-evidence bytes and exposes their
byte size and SHA-256. Strict decoding, a separately modeled attempt identity,
and manifest-backed resolution remain planned. Evaluation and task identities
are retained but not interpreted as queue, retry, or lifecycle state.

Absent attempt identifiers must be represented explicitly as unavailable, not
fabricated from a simulation or artifact ID.

## Native and normalized layers

Provider integrations remain responsible for parsing native artifacts and
producing normalized domain observations. SCF evidence for a spin-polarized
calculation retains spin-channel populations or observed total magnetization
when the calculator reports them and records explicitly when it does not. The
protected relaxation observation must contain at least the final base
`UnitCell`, terminal status, ionic convergence status, force and stress
observations when represented, observed spin information when represented, and
normalization provenance. Its result must distinguish provider completion from
scientific or workflow acceptance.

The protected evidence package may store those normalized values and neutral
artifact identities but must not import QE, VASP, pymatgen, mp-api, or another
outward implementation.

```text
provider bytes -> outward parser -> normalized observation
                                      |
                                      v
                             neutral evidence record
```

Retained provider bytes remain immutable artifacts. Re-parsing creates new
normalization evidence; it does not rewrite the original artifact record.

## Integrity and storage

The evidence codec and manifest loader will follow the simulation and structure
library fail-closed rules: strict versioned schemas, canonical bytes, bounded
files, exact size and digest checks, path containment, symlink rejection,
complete-record selection, and ambiguity failure.

Artifact locations are storage references, not identities. Local absolute paths
must not appear in portable evidence documents. An artifact record uses stable
logical identity, byte size, SHA-256, media type, and declared role. Storage
adapters may map that identity to a local or remote object outside the neutral
contract.

## Compatibility qualifications

Evidence records preserve facts; they do not infer that evidence is suitable
for subtraction or comparison. A separate pure qualification operation must
compare the relevant scientific-specification fields and exact prepared
calculator inputs before derived analysis consumes several records. Any
permitted difference, such as distinct k-point meshes appropriate to different
elemental cells, must be explicit in the qualification policy and result.

## Publication of relaxed structures

`PwDftRelaxedStructurePublisher` is the pure deliberate action that consumes a
relaxation result and matching evidence and creates:

1. deterministic general-`UnitCell` structure bytes;
2. a new `StructureRecord`;
3. provenance referencing the exact starting structure, relaxation
   `SimulationRecord`, scope, and evidence record; and
4. derivation metadata distinguishing ion-only from full relaxation without
   mislabeling either result as pristine, primitive, or conventional.

For `ATOMIC_POSITIONS`, the result verifies that the final lattice equals the
starting host lattice under the schema's exact normalized lattice
representation. For `ATOMIC_POSITIONS_AND_CELL`, the result retains the
observed final lattice and requires explicit cell convergence state. The
publisher verifies evaluation/task correlation and the exact canonical
normalized-observation digest. It returns bytes and a record; it never writes or
mutates a structure catalog.

## Required verification

Tests must cover exact encoding, malformed records, missing simulation and
calculator-input correlations, artifact digest mismatch, multiple attempts,
normalization provenance, relaxed-structure publication provenance, ambiguity,
path and symlink rejection, and absence of runtime or provider imports. All
tests use synthetic or retained evidence and must not execute a calculator.
