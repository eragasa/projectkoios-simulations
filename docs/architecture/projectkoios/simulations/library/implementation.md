# Simulation library implementation rules

## Planned production modules

```text
src/python/projectkoios/simulations/library/
  __init__.py
  record.py
  codec.py
  library.py
```

- `record.py` will define `SimulationRepresentation`, `SimulationProvenance`,
  and `SimulationRecord`.
- `codec.py` will own one strict codec for each supported representation.
- `library.py` will define `SimulationLibraryEntry`, `SimulationResolution`,
  `SimulationLibrary`, `SimulationLibraryManifestLoader`, and domain-specific
  manifest, absence, conflict, and integrity failures.

These names are architectural commitments, not currently importable APIs.

## Version-one decision packet

The bounded architecture council converged on these version-one boundaries:

- a specification stores one complete `StructureRecord`, but not duplicate
  `UnitCell` bytes;
- `SimulationResolution` supplies the matching verified `StructureResolution`
  and decoded cell to calculator-input translators;
- the existing `PseudopotentialFile` and byte-verifying
  `PseudopotentialLibrary` remain the one exact pseudopotential dependency and
  resolver rather than gaining a parallel record hierarchy;
- `PseudopotentialFile` includes an explicit protected-core artifact format and
  format version where required, so translation never guesses UPF versus VASP
  POTCAR semantics from a filename or provider subtype;
- calculation stage leaves shared `PwDftSimulation`; the enclosing SCF or
  relaxation specification and relaxation scope own it exactly once;
- canonical neutral spin intent represents unpolarized, collinear,
  noncollinear, and spin-orbit-coupled modes, while each translator either
  exhaustively supports a mode or rejects it explicitly; and
- every recipe coordinate that changes scientific content creates distinct
  canonical specification bytes and a deterministic derived
  `SimulationRecord`, even when that record is not persisted in a catalog.

The atomic migration order is schema decisions first, then—in one unreleased
repository-wide change—specification codecs and records, request replacement,
derived identities, and projector return types. No projector may construct a
placeholder source digest from the flattened request. Provider mapping gates
must pass before version-one identities become public and immutable. Manifest
persistence and removal of tool-side reconstruction follow that atomic change.

## Specification locations

The scientific payload types belong with their domains rather than in the
library package:

```text
projectkoios.simulations.dft.pw.simulation
projectkoios.simulations.dft.pw.scf.specification
projectkoios.simulations.dft.pw.scf.request
projectkoios.simulations.dft.pw.relaxation.specification
projectkoios.simulations.dft.pw.relaxation.request
```

`PwDftSimulation` will own calculator-neutral structure,
`delta_n_electrons`, spin, exchange-correlation, occupation, and
pseudopotential requirements shared by SCF and relaxation. Stage-specific
specification records will own sampling, relaxation scope, and convergence
controls. Occurrence requests will add only the identities and context required
to request an evaluation.

`delta_n_electrons` is an explicit built-in integer relative to the neutral
electron count implied by the same nuclei and exact pseudopotentials. Positive
values add electrons and negative values remove them. When a simulation binds a
`UnitCellDefectDelta`, it must satisfy
`defect.charge_state == -simulation.delta_n_electrons`. The initial schema does
not represent fractional net electron changes.

## Spin specification

Spin is calculator-neutral scientific input, not an input-rendering default. A
simulation specification records whether the calculation is unpolarized,
collinear spin-polarized, noncollinear, or spin-orbit coupled. A spin-polarized
specification separately records the intended difference between spin-up and
spin-down electron counts, whether that difference is constrained or only an
initial condition, and any site-resolved initial moments needed to reproduce
the prepared calculation.

Neutral substitutional phosphorus in silicon is an explicit collinear
spin-polarized doublet: it has one more electron in one spin channel than the
other. This remains true with `delta_n_electrons == 0`, because the fifth
phosphorus valence electron is already part of the neutral substituted cell.
Every ideal, ion-only, fully relaxed, and final-SCF Si:P specification must
retain the same declared spin state unless a separately identified study is
deliberately comparing spin states.

## Deterministic representation

Each representation receives an explicit versioned JSON schema. The codec must:

- accept and emit UTF-8 only;
- reject duplicate keys, unknown keys, missing keys, non-finite numbers, and
  implicit defaults;
- use one canonical member order and compact separators;
- end the encoded document with one newline;
- encode scientific quantities with explicit units and schema-defined numeric
  lexical forms; and
- decode to the exact expected specification type.

The committed bytes, rather than a reserialized in-memory object, are the
integrity authority. A codec round trip must reproduce those bytes exactly.
Schema evolution creates a new schema version; it never silently changes the
meaning of an existing version.

## Manifest and resolution

The manifest will use one strict schema version and complete key sets. Each
entry binds one `SimulationRecord` to one normalized relative `.json` path
beneath an explicit library root.

Resolution must proceed in this order:

1. select a complete record, or require a unique stable ID;
2. reject missing files, symlinks, non-regular files, and path escape;
3. enforce manifest and record byte limits;
4. verify exact byte size and SHA-256;
5. decode with the representation-specific codec;
6. verify the embedded stable ID and representation;
7. verify every referenced structure and pseudopotential record identity; and
8. return an immutable `SimulationResolution`.

Dependency verification may consume caller-supplied neutral structure and
pseudopotential libraries. The simulation library must not search arbitrary
filesystem roots or substitute a record that merely has the same friendly ID.

## Calculator-input boundary

Before evidence can identify how a calculation was prepared, the protected core
requires a neutral `CalculatorInputRecord`. This record answers a plain question:
which exact input files and required external files were prepared from which
exact simulation specification for which calculator integration?

The record contains the integration identity, input-format and schema versions,
exact `SimulationRecord`, rendered-input artifact identities, unresolved
external-input identities, byte sizes, SHA-256 values, and provenance. It
contains no QE or VASP-native model object.

QE, VASP, and other outward integrations remain responsible for translating a
neutral request into their native files and creating this neutral record. The
current Python APIs call that translation an “input projection”; new
architecture prose uses “calculator-input translation” or “input rendering.” A
simulation record cannot reference or import an integration type, and
machine-local executable and pseudopotential roots remain injected deployment
configuration.

Each calculator-input translator must map the neutral
`delta_n_electrons` convention into the calculator's native charge or electron
count convention explicitly. It must not pass the signed integer through by
name alone. The resulting `CalculatorInputRecord` preserves the rendered native
value so evidence can verify what was requested.

## Atomic migration

The implementation sequence is:

1. extend `StructureLibrary` with an exact general `UnitCell` representation
   and derivation provenance for ideal, ion-relaxed, and fully relaxed cells;
2. define a protected neutral relaxation observation/result and outward QE/VASP
   normalization adapters;
3. define the protected exact `CalculatorInputRecord` and outward calculator
   input translation, including charge and spin translation for SCF and both
   relaxation scopes;
4. freeze simulation schemas and dependency-reference rules;
5. introduce SCF and relaxation specification records;
6. atomically change existing request records to contain specifications;
7. update recipes, workflows, integrations, tools, examples, and tests in the
   same change;
8. add the manifest-backed simulation library; and
9. remove tool-side reconstruction of neutral requests.

No simultaneous old/new request API, compatibility alias, or alternate library
is allowed.

## Required verification

Tests must cover canonical bytes, all malformed schema cases, byte limits,
size and digest mismatches, traversal, symlinks, ambiguity, representation
mismatch, embedded-ID mismatch, missing dependencies, exact dependency
mismatch, schema-version rejection, and deterministic round trips. Repository
gates must prove that the protected library imports neither workflows nor
integrations and that resolving a record performs no calculator execution.
