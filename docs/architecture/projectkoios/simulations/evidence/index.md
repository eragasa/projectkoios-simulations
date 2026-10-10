# Immutable simulation evidence

## Status

An initial protected-core implementation now supplies exact artifact references,
normalization provenance, and immutable `SimulationEvidenceRecord` correlation.
Existing SCF/relaxation results and execution records remain authoritative in
their current domain modules. Relaxation publication now verifies evaluation,
task, artifact, canonical normalized-observation, and canonical whole-evidence
correlation. Atomic SCF adoption, strict evidence decoding, outward QE/VASP
normalization adapters, attempt identity, and a manifest-backed evidence library
remain to be implemented.

## Purpose

Simulation evidence correlates one exact scientific specification with the
exact calculator input files prepared from it, execution facts, native
artifacts, and normalized observations produced by one completed evaluation. It
makes a retained result
inspectable without turning that result into workflow state or scientific
acceptance.

Evidence is downstream of execution and upstream of derived analysis:

```text
SimulationRecord + CalculatorInputRecord
                       |
                       v
              completed evaluation
                       |
                       v
          SimulationEvidenceRecord
                       |
                       +--> convergence observations
                       +--> formation-energy inputs
                       `--> reproducibility inspection
```

## Evidence contents

A record must distinguish:

- the complete neutral `SimulationRecord`;
- the exact `CalculatorInputRecord` identifying rendered input files;
- workflow evaluation or occurrence correlation;
- calculator integration and version observations;
- mechanical execution facts;
- exact native artifact identities;
- provider-normalized scientific observations; and
- provenance of the retained evidence document itself.

An evidence record may refer to externally retained artifact bytes by exact
size and SHA-256. It must not claim the bytes remain available unless their
storage location has been verified separately.

## Separation from specifications and structures

Calculated energies do not enter `SimulationLibrary`. A relaxed structure does
not replace the original structure record silently. Publishing an ion-relaxed
or fully relaxed structure requires a new exact base-`UnitCell`
`StructureRecord` whose provenance references the starting structure,
relaxation specification, relaxation scope, and qualifying evidence. Ion-only
relaxation must preserve the exact declared host lattice; full relaxation may
change both lattice and positions under declared pressure controls.

Likewise, evidence from two attempts does not overwrite either attempt. Each
immutable record remains independently addressable.

## Non-goals

The evidence layer does not own:

- queues, retries, leases, mutable status, cancellation, or delivery;
- calculator credentials, executable discovery, or execution authority;
- provider parsing or native input generation;
- convergence or formation-energy acceptance policy;
- a guarantee of numerical correctness; or
- a claim that differently projected calculations are scientifically
  compatible.

See [`implementation.md`](implementation.md) for the planned record and codec
rules and [`schematics.md`](schematics.md) for evidence and authority flows.
