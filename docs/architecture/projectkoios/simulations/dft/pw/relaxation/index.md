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

`PwDftRelaxationDegreesOfFreedom` and `PwDftCellRelaxationMode` already require
an explicit calculator-neutral cell-relaxation mode. The implemented closed set
distinguishes fixed cell, volume only, shape at fixed volume, selected strain
components, and unrestricted lattice vectors. Selected-component mode carries
an explicit six-component mask. No default is inferred from a calculator.

The protected contract validates the declared choice but does not select which
mode a silicon or another scientific campaign will use. Provider capability and
projection remain separately qualified.

## Symmetry and initialization

Relaxation specifications must explicitly record symmetry constraints,
initial atomic displacement policy, starting spin state, and whether several
initial conditions form separate calculations. These fields prevent provider
defaults from silently restricting a defect relaxation. Selection of one policy
for the silicon studies remains workflow-owned.

## Bulk qualification boundary

The protected records retain exact requests, normalized observations, result
correlation, and pure publication. They do not decide that a structure is
zero-pressure qualified or that numerical settings transfer from its starting
lattice. The planned
[`pw_dft_bulk_qualification`](../../../workflows/pw_dft_bulk_qualification/index.md)
composition uses public relaxation and SCF workflow contracts to assess force,
pressure residual, allowed cell changes, and fresh final-setting confirmation.
The protected core does not import that workflow.

The existing relaxation specification remains unchanged. Bulk qualification
references an additive neutral wavefunction and density/potential cutoff
realization. First-party adapter evidence proves that the exact provider input
realizes it; QE `ecutrho` and `charge_density_cutoff_ratio` do not enter
protected relaxation records or the neutral terminal handoff.

## Authority boundary

The neutral request, observation, and result do not execute a calculator.
Outward integrations render inputs and normalize retained outputs; an external
runtime owns execution authority and lifecycle.

See [`implementation.md`](implementation.md) for planned modules,
[`schematics.md`](schematics.md) for request/evidence/publication flows,
[`scientific.md`](scientific.md) for interpretation limits, and
[`numeric.md`](numeric.md) for convergence and consistency requirements.
