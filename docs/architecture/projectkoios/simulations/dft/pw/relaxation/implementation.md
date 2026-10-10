# Plane-wave DFT relaxation implementation rules

## Production module map

```text
src/python/projectkoios/simulations/dft/pw/relaxation/
  __init__.py
  base.py
  capabilities.py
  integration.py
  observation.py
  result.py
  publication.py
```

The request, observation, result, and publication contracts are implemented.
Provider output-normalization adapters and richer cell-relaxation modes remain
future work.

## Observation fields

`PwDftRelaxationObservation` is a frozen, slotted dataclass. It contains
normalized values only and imports no QE or VASP type. Each optional physical
quantity uses an explicit unavailable state or `None` according to one reviewed
schema; missing values are never synthesized as zero.

The final structure is a base PhysKit `UnitCell`. It does not claim primitive,
conventional, pristine, or relaxed-library representation by its Python type.
Its scientific role follows from the request scope and evidence.

Terminal status, ionic convergence, cell convergence, and parser consistency
are separate fields. Validation rejects contradictory combinations while
allowing a completed provider run that failed convergence.

## Result and evidence correlation

`PwDftRelaxationResult` binds:

- one exact relaxation request;
- an exact prepared `CalculatorInputRecord`;
- one normalized observation; and
- exact native artifact identities.

It emits deterministic version-one canonical observation JSON including the
final base `UnitCell`, occurrence identifiers, scope, mechanical facts, program
version, and artifact identities. `PwDftRelaxedStructurePublisher` requires the
`SimulationEvidenceRecord.normalization` identity to match those bytes exactly.
The result stores no retry count, queue state, lease, mutable status, or reusable
execution authority.

## Exact structure publication

The publisher verifies the exact starting structure against the relaxation
simulation, correlates prepared-input source and digest, calculator integration
and name, program version when observed, native artifacts, provider completion,
mechanical convergence, and canonical normalization digest. It then emits
canonical `unit-cell` bytes and `ObservedStructureProvenance` referencing the
exact starting record, calculation specification, complete canonical evidence
record, scope, and stable publication operation.

This is a pure transformation. It writes no catalog or structure file, grants no
calculator authority, and applies no force, pressure, or scientific acceptance
threshold beyond the retained convergence facts.

## Outward adapters

QE normalization adapts `QeRelaxData`, its trajectory, QEXSD final structure,
execution record, and consistency observations into the neutral observation.
VASP normalization adapts `VaspRelaxData` and future complete relaxation output
evidence. Provider-specific parsers remain outward.

Provider adapters must identify which source supplied every normalized value and
must retain disagreements rather than silently choosing between stdout, XML,
or other files.

## Fixed-cell normalization

For `ATOMIC_POSITIONS`, the exact starting lattice is authoritative. The
normalized final structure combines that exact lattice with observed final
positions. Any provider-reported lattice becomes a consistency observation.
This avoids changing exact structure identity solely because of native output
precision while detecting an unexpected cell change.

## Variable-cell normalization

For `ATOMIC_POSITIONS_AND_CELL`, the final provider-observed lattice and
positions form the normalized structure. The observation retains target and
final pressure/stress information and the explicit allowed cell-relaxation
mode. A result lacking the required final cell cannot qualify for structure
publication.

## Spin and charge

The request/specification explicitly contains `delta_n_electrons` and spin
intent. The prepared input record proves how those values were rendered. The
observation retains provider-reported total magnetization or spin populations
when available. Relaxation evidence with incompatible charge or spin cannot be
bound into the same defect energy series.

## Required verification

Tests must cover provider completion versus convergence, unavailable forces and
stress, final-structure source correlation, fixed-cell lattice preservation,
variable-cell final lattice, contradictory sources, charge/spin correlation,
trajectory identity, malformed observations, provider adapter normalization,
and absence of calculator execution.
