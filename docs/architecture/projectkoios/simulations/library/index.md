# Exact manifest-backed simulation library

## Status

This node specifies a target protected-core capability. The production
`projectkoios.simulations.library` package and its public records do not yet
exist. Documentation precedes implementation so the new library can reuse the
existing SCF and relaxation domain contracts rather than introduce a competing
simulation hierarchy.

## Purpose

`SimulationLibrary` will catalog immutable, calculator-neutral calculation
specifications. It will provide exact identity, deterministic representation,
integrity verification, provenance, and typed resolution for plane-wave DFT
SCF and relaxation specifications.

The library will not catalog workflow occurrences, provider-native input,
execution state, results, scientific acceptance, or calculator authority.

## Scientific specification boundary

A reusable calculation specification and a request to evaluate it are distinct:

```text
PwDftScfSpecification                         PwDftScfRequest
  scientific model                              evaluation_id
  SCF sampling                    +              specification

PwDftRelaxationSpecification                  PwDftRelaxationRequest
  scientific model                              evaluation_id
  sampling and relaxation controls +             specification
```

The library stores the specification on the left. The request on the right is
an occurrence envelope created by workflow composition. An `evaluation_id` is
therefore never part of a specification's content identity.

The specification types will be introduced by atomically refactoring the
existing `PwDftScfRequest` and `PwDftRelaxationRequest` contracts. Parallel old
and new request shapes, aliases, and compatibility facades are not permitted.

## Exact record identity

A planned `SimulationRecord` carries:

- a stable qualified `simulation_id` used for human and manifest lookup;
- a `SimulationRepresentation` distinguishing SCF and relaxation payloads;
- a representation-specific schema version;
- exact byte size and lowercase SHA-256;
- immutable closed authored, transferred, or derived provenance retaining the
  exact result digest and its applicable source or parent identities.

`simulation_id` alone is not an exact identity. A library may retain multiple
historical records with the same stable identifier. Unique lookup must fail on
ambiguity; exact lookup requires the complete record.

## Exact dependencies

A simulation payload references a complete `StructureRecord` and complete
`PseudopotentialFile` identities, not only friendly IDs, chemical formulas,
filenames, or local paths. Consequently, changing a structure or
pseudopotential requirement changes the simulation payload and its SHA-256.

The payload explicitly records `delta_n_electrons` even when it is zero.
Positive values mean electrons added relative to the neutral electron count for
the exact structure and pseudopotentials; negative values mean electrons
removed. This electronic count is part of exact simulation identity. When the
structure comes from a declared defect delta, the exact specification requires
`defect.charge_state == -simulation.delta_n_electrons`. Spin treatment is also
exact specification data. In particular, neutral Si:P records require a
spin-polarized doublet rather than inheriting a calculator's non-spin-polarized
default.

The payload contains no executable path, scratch directory, installed
pseudopotential root, credential, API key, or provider-native prefix. Resolution
of machine-local files and translation into QE, VASP, or another calculator's
input files remains outside this library.

## Non-goals

`SimulationLibrary` does not:

- construct or authorize an execution;
- choose QE, VASP, or another calculator;
- store calculator-specific input-rendering profiles;
- assign workflow occurrence or attempt identities;
- store queues, leases, retries, cancellation, or delivery state;
- store calculated energies or relaxed structures;
- infer scientific convergence or acceptance; or
- select elemental chemical-potential phases.

See [`scientific.md`](scientific.md) for the frozen version-one scientific
schema, [`implementation.md`](implementation.md) for the planned module and
migration rules, and [`schematics.md`](schematics.md) for identity and
dependency flows.
