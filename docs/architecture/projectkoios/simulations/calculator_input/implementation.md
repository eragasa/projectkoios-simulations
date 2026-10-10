# Prepared calculator-input implementation rules

## Current module map

```text
src/python/projectkoios/simulations/calculator_input/
  __init__.py
  artifact.py
  record.py
```

- `artifact.py` defines immutable rendered-artifact and external-input
  requirement records.
- `record.py` defines source references, neutral-to-native mapping provenance,
  `CalculatorInputRecord`, and deterministic aggregate identity. Representation
  is an explicit nonempty string because outward integrations are extensible;
  each record's schema version qualifies its meaning.

## Acyclic simulation reference

`SimulationRecord` payloads must not depend on prepared inputs. To prevent a
cycle, `CalculatorInputRecord` stores a local immutable simulation content
reference containing stable simulation ID, representation, schema version,
byte size, and SHA-256. Its constructor or preparation action validates that
reference against the caller-supplied complete `SimulationRecord` once the
simulation-library migration supplies that record. The current constructor
validates the reference's exact identity fields but cannot resolve a simulation
catalog that does not yet exist.

## Rendered artifacts

Each `CalculatorInputArtifact` requires:

- normalized basename and semantic role;
- media type and encoding;
- exact byte size and lowercase SHA-256; and
- immutable bytes or a verified storage-independent content reference.

Filenames must be unique. Ordered artifact identity is retained because some
calculator input sets use ordering semantically. The aggregate record digest is
computed from a versioned canonical document that contains every artifact and
external-input record identity.

## External inputs

An external requirement never stores only `Si.upf`, `POTCAR`, or another
basename. It binds the required role to a complete scientific file identity,
including element where applicable, format, stable ID, byte size, SHA-256, and
provenance. Machine-local resolution into a path is a separate deployment
operation and cannot change the prepared record.

## Mapping observations

Charge and spin preparation records contain:

- neutral field and value;
- native destination field or fields;
- exact rendered native value;
- mapping qualification; and
- whether the value is constrained, initialized, or merely enables a mode.

This makes sign conversion and spin realization inspectable without importing a
provider-native model into protected core.

## Integration migration

Existing `PwDftScfInputProjection` and `PwDftRelaxationInputProjection` remain
the immediate typed rendering results until an atomic migration changes them to
return or contain a `CalculatorInputRecord`. QE and VASP integrations must create
the record from the exact rendered bytes rather than reconstructing it later
from configuration objects. The current QE/VASP SCF translators now derive
charge and spin fields from neutral declarations, but still return the older
rendered-input record and therefore cannot yet satisfy evidence correlation.

The migration updates integration protocols, SCF and relaxation composition,
tools, examples, tests, and evidence correlation in one change. No parallel
legacy and exact-input APIs or compatibility facade is introduced.

## Integrity and authority

Construction verifies artifact bytes against every declared digest and rejects
unknown or duplicate roles, ambiguous external requirements, missing simulation
correlation, and unsupported schema versions. It performs no filesystem search
or executable invocation.

Possessing a `CalculatorInputRecord` is not execution authority. A separate
external runtime must still resolve deployment paths and receive explicit
calculator authorization.

## Required verification

Tests must cover deterministic aggregate identity, changed ordering, changed
bytes, duplicate basenames and roles, traversal, malformed hashes, missing
external identities, simulation-reference mismatch, QE/VASP charge-sign
mapping, spin-mode and doublet mapping, and calculator-free construction.
