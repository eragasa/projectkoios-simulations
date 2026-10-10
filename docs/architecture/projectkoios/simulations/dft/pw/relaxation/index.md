# Calculator-neutral plane-wave DFT relaxation

## Status

The protected relaxation domain defines requests, scope, sampling, convergence
policy, normalized terminal observations, native-artifact identity,
request/input/result correlation, canonical observation bytes, and pure exact
relaxed-structure publication. QE normalization now covers terminal geometry,
energy, maximum force, stress, pressure, magnetization, and provider version.
VASP normalization and complete per-atom normalized force vectors remain to be
implemented before these records support complete provider-independent defect
workflows.

## Existing request contract

`PwDftRelaxationRequest` binds:

- a plane-wave DFT simulation;
- `ATOMIC_POSITIONS` or `ATOMIC_POSITIONS_AND_CELL` scope;
- k-point and wavefunction-cutoff sampling; and
- energy, force, step, pressure, and pressure-tolerance controls.

Fixed-cell relaxation forbids pressure controls. Variable-cell relaxation
requires target pressure and pressure tolerance.

## Observation

`PwDftRelaxationObservation` represents normalized facts from one retained
provider result:

- terminal provider status;
- ionic convergence observation;
- final base `UnitCell`;
- final energy when represented;
- final forces and maximum force when represented;
- a unit-aware PhysKit `StressTensor` and scalar pressure when represented;
- ionic step count and trajectory artifact identity;
- spin or magnetization observations when represented;
- native artifact identities; and
- normalization provenance.

Unavailable provider facts are explicit. Completion is not automatically ionic
convergence, and ionic convergence is not workflow or scientific acceptance.

## Result and exact publication

`PwDftRelaxationResult` correlates the request, exact `CalculatorInputRecord`,
normalized observation, and native artifacts. Its version-two canonical
observation bytes make the normalized geometry and mechanical facts
content-addressable. Stress is canonicalized to pascals with tension-positive
components for serialization and comparison; the runtime tensor remains
unit-aware and native calculator evidence retains native units and convention.

`PwDftRelaxedStructurePublisher` correlates that result with an exact starting
`StructureResolution` and a `SimulationEvidenceRecord`. It rejects unmatched
prepared-input sources, native artifacts, calculator identity, convergence
facts, and normalization digests. It returns canonical base-`UnitCell` bytes
and a `StructureRecord` with `ObservedStructureProvenance`; it performs no file
write and does not mutate `StructureLibrary`.

## Cell degrees of freedom

`ATOMIC_POSITIONS_AND_CELL` currently says only that cell degrees are available.
The specification must be extended with an explicit cell-relaxation mode before
defect manifests are frozen. The closed set must distinguish at least volume-
only, shape at fixed volume, constrained lattice components, and unrestricted
lattice-vector relaxation. No default is inferred from a calculator.

This document records the required explicit choice but does not select which
mode the Si:P and Si:B study will use.

## Symmetry and initialization

Relaxation specifications must explicitly record symmetry constraints,
initial atomic displacement policy, starting spin state, and whether several
initial conditions form separate calculations. These fields prevent provider
defaults from silently restricting a defect relaxation. Selection of one policy
for the silicon studies remains workflow-owned.

## Authority boundary

The neutral request, observation, and result do not execute a calculator.
Outward integrations render inputs and normalize retained outputs; an external
runtime owns execution authority and lifecycle.

See [`implementation.md`](implementation.md) for planned modules,
[`schematics.md`](schematics.md) for request/evidence/publication flows,
[`scientific.md`](scientific.md) for interpretation limits, and
[`numeric.md`](numeric.md) for convergence and consistency requirements.
