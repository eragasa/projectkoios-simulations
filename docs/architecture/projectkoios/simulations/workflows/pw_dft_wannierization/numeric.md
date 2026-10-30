# Plane-wave DFT Wannierization numerical contract

## Purpose

The planned numerical contract defines exact identity, ordering, cardinality,
and dimensional checks needed to correlate a provider-neutral route. It does
not prescribe material settings, physical convergence thresholds, localization
tolerances, interpolation-error tolerances, or acceptance policy. Those values
belong to the consuming scientific project and must be declared before its
evidence is evaluated.

Exact checks and tolerance-based scientific comparisons remain distinct. Byte
identity, integer dimensions, enumerated roles, source order, and parent hashes
are exact. Floating-point comparisons require an explicit quantity, unit,
metric, tolerance, and non-finite-value policy owned by the consuming analysis.

## Accepted bulk predecessor invariants

Before a parent handoff is eligible, correlation requires one exact accepted
bulk qualification identity containing:

- the final exact structure record;
- the final neutral wavefunction and density/potential cutoff realization;
- the final realized `PwDftKPointSamplingPolicy`;
- exact provisional, relaxation, and final-confirmation evidence lineage;
- confirmation that the selected setting is scoped to the final structure; and
- an accepted rather than provisional, failed, inconclusive, or
  budget-exhausted disposition.

`Q0@S0` cannot be relabeled as qualified on a relaxed `S1`. If confirmation on
`S1` changes the setting to `Q1`, this route rejects the predecessor until bulk
composition has produced a new relaxation and confirmation under `Q1`. Equal
integer mesh tuples, rounded lattice parameters, or friendly IDs do not satisfy
this check.

## Reciprocal-grid invariants

A uniform-grid declaration records:

- the exact source-ordered reciprocal coordinates;
- coordinate convention and reciprocal basis identity;
- one finite positive weight per point and the declared normalization rule;
- grid dimensions, offset, symmetry policy, and time-reversal policy;
- spin-component inventory; and
- the exact parent-state identity.

An adapter must not silently sort, deduplicate, symmetry-reduce, or regenerate
the point list after identity is established. If a provider reports the same
points in another order, correlation requires an explicit bijective
permutation. Approximate coordinate matching uses a prospectively declared
coordinate metric and tolerance; it must reject ambiguous multiple matches.

## Cross-stage cardinality

The route tracks separate nonnegative or positive integer quantities as
applicable:

```text
N_k       reciprocal-point count
N_b       parent or interface band count
N_w       Wannier rank
N_p       projection-function count
N_n(k)    neighbor count for source point k
N_R       real-space lattice-vector count
N_s       spin-component count
```

The workflow does not assume `N_b == N_w` or `N_p == N_w`. Disentanglement may
produce a rectangular transformation from an outer band space into a retained
subspace. Selective localization or another unsupported construction must be
rejected or represented by a separately reviewed contract rather than forced
into square-matrix assumptions.

## Neutral artifact-role closure

Each handoff declares a closed selected-retained-evidence role inventory. The
accepted first profile requires one NNKP, one EIG, one AMN, one MMN, one WOUT,
and one real-space Hamiltonian. It requires the unitary and disentanglement
matrix roles exactly when the construction declares the corresponding
transformations. It does not assert that a provider's private work directory
contains no incidental files. Every required role has exactly one producer and
at least one declared consumer. Other optional roles are qualified by route
kind; they are not globally mandatory merely because one provider can produce
them. A component-operator
extension that declares plane-wave
coefficients must additionally bind their dimensions, ordering, normalization
convention, parent-state identity, and correlation with the same source-ordered
eigenstate basis used by the gauge/disentanglement observations. A sampled
real-space wavefunction role instead binds its grid, origin, periodicity,
normalization, band/component ordering, and provider semantics. A transform
between the two representations is separate evidence and must not be inferred
from matching cardinalities.

Correlation rejects:

- a missing required role;
- an undeclared extra selected retained-evidence role when the handoff is
  closed;
- duplicate logical identities or duplicate physical artifacts where
  independence is required;
- changed byte size or digest;
- a role supplied by the wrong occurrence;
- a parent or seed identity mismatch; and
- a storage path used as a substitute for artifact identity.

Native suffixes and basenames remain outward-provider details. An outward
adapter may map a neutral role to a provider-native file, but the workflow
contract compares the neutral role and exact artifact reference rather than
importing the native file class.

## Normalized dimension checks

Before representation evidence can be assembled, normalized observations must
support the following checks as applicable to the declared route:

- reciprocal-point counts and source order agree across the Bloch frame,
  neighbor topology, interface eigenvalues, overlaps, projection observations,
  gauge observations, and localization result;
- band counts agree among parent eigenvalues and every interface observation
  that is defined on the parent band inventory;
- Wannier rank agrees among the construction declaration, localization centers
  and spreads, square gauge transformations, and real-space Hamiltonian blocks;
- a disentanglement observation has declared source and target dimensions
  compatible with the outer band inventory and Wannier rank;
- the ordered neighbor inventory agrees between topology and overlap
  observations, including source, target, and reciprocal-lattice shift;
- real-space Hamiltonian blocks are square in the declared orbital order and
  carry one declared degeneracy per lattice-vector entry; and
- spin components are neither merged nor replicated implicitly.

A parser's successful construction is evidence about its own native contract,
not automatic proof that all route-level dimensions agree. Route correlation
consumes normalized observations and reports each mismatch explicitly.

## Exact lineage checks

Every child handoff carries exact predecessor identities. A representation
correlation must prove one unbroken chain through:

1. the accepted bulk qualification and exact final structure/setting pair;
2. the parent simulation and prepared input;
3. the parent occurrence and retained evidence;
4. the uniform-grid declaration and normalized frame;
5. the preprocessing declaration and normalized topology;
6. the interface declaration and normalized interface evidence; and
7. the localization declaration and normalized localization observation.

The five route occurrences begin with the parent SCF after the predecessor
pair is accepted. Bulk convergence and relaxation occurrences are not counted
as interface-route stages, and none of their completion statuses authorizes a
route occurrence.

Two artifacts with compatible dimensions but different parent, structure,
pseudopotential, reciprocal grid, spin branch, construction declaration, or
occurrence identity are incompatible. A retry is a new attempt identity and is
not allowed to overwrite the earlier failure. A changed scientific coordinate
creates a new specification rather than a retry.

## Floating-point and non-finite values

Normalized quantities retain source precision, unit, and provenance. The
workflow does not round values before identity or comparison. Any
consumer-owned comparison must define:

- absolute, relative, mixed, norm-based, projector-based, or another metric;
- unit conversion and canonical unit;
- scalar energy alignment separately from subspace alignment;
- treatment of degeneracies and ambiguous state correspondence;
- behavior at exactly the tolerance boundary; and
- rejection or explicit classification of NaN and infinite values.

Default tolerances must not be inferred from machine epsilon, display
precision, a provider's process-success marker, or values observed after a run.
A provider-reported localization threshold is retained as part of the exact
construction declaration; satisfying it does not establish a downstream
interpolation threshold.

## Numerical outcomes

Route-level numerical correlation may report only bounded consistency outcomes,
such as complete, inconsistent, unsupported, or inconclusive, together with
exact reasons and source identities. It does not report a scientific
representation as accepted. A consumer's numerical verification may compare
construction and withheld sets, velocities, curvature, effective masses,
projectors, or represented operators, but those policies and thresholds are
outside this reusable workflow contract.

No check in this document grants calculator execution. Software tests use
synthetic values, fake executables in the owning execution/provider layers, or
retained artifacts. Passing them does not establish numerical convergence or
scientific validation.
