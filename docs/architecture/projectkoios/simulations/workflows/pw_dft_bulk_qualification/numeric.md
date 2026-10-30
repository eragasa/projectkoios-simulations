# Plane-wave DFT bulk qualification numerical contract

This document constrains a planned, unimplemented capability. It does not add a
schema or API, execute calculations, or establish numerical convergence.

## Exact identity domains

Every numerical observation and decision is bound to an exact tuple containing,
at minimum:

```text
structure identity
+ scientific-model/specification identity
+ pseudopotential identities
+ occupation, spin, and symmetry policy
+ existing wavefunction-cutoff/grid coordinate
+ neutral wavefunction and density/potential cutoff realization
+ existing realized k-point sampling policy
+ projected request, prepared-input, and occurrence identities
+ normalized evidence and artifact identities
+ assessment-policy identity
```

Changing any member creates a different qualification domain. A friendly
campaign ID, storage path, provider basename, equal displayed energy, or equal
integer k-point tuple is not sufficient identity.

## Initial joint study

The initial study on seed structure `S0` uses the existing
`PwDftScfGridConvergenceRecipe`. Each coordinate contains its existing cubic
mesh density and wavefunction cutoff. A neutral coupled-cutoff realization
declares the corresponding density/potential basis setting; provider adapter
evidence proves each projected input realizes it.

The existing `EnergyGridConvergenceAssessor` inspects both high-coordinate
edges, and the existing controller extends, accepts, or exhausts the grid. A new
typed correlation binds every supplied observation to the exact structure,
request/specification, prepared input, selected occurrence, normalized evidence
bytes, adapter mapping, and unchanged assessment. Only an accepted correlation produces `Q0@S0`; its production setting is the
highest tested mesh/cutoff corner. The current assessment alone is not
structure-scoped.

## Mechanical structure assessment

For a variable-cell result, the mechanical assessment records:

- exact starting and final structure identities;
- declared and observed cell mode;
- initial and final lattice and volume observations;
- provider completion and optimizer convergence separately;
- finite final maximum force and its recomputed comparison with the declared
  criterion;
- finite scalar target pressure, final pressure, and unrounded residual
  `abs(p_final - p_target)` with a recomputed threshold comparison;
- complete finite normalized stress tensor and sign/unit convention;
- finite, nonsingular, positively oriented final-cell checks;
- disallowed cell-component changes;
- native artifact and normalization identities; and
- missing, inconsistent, passed, or failed status for each required fact.

A provider convergence marker cannot substitute for a missing force or pressure
observation. Equality at a threshold follows an explicitly declared inclusive
or exclusive comparison rule.

## Final confirmation stencil

A single calculation at the candidate coordinate cannot demonstrate a
neighboring-point convergence criterion. Final confirmation on exact structure
`S1` requests the candidate plus enough prospectively declared stricter
cutoff/sampling context to re-evaluate the original joint tolerance and stable
window. Reusing retained observations is allowed only when their exact structure
and every other qualification-domain identity match `S1`.

The confirmation result is scoped as `Q1@S1`. It records whether:

- the candidate remains accepted under the same selection rule;
- additional coordinates are required;
- a different or tighter setting is selected;
- evidence is inconsistent or unavailable; or
- the confirmation budget is exhausted.

## Stable-pair feedback rule

The planned composition applies the following fail-closed rule:

```text
S0
  -> provisional joint qualification Q0@S0
  -> relaxation under Q0
  -> mechanically qualified S1
  -> confirmation Q1@S1

if Q1 confirms Q0:
    accept exact pair (S1, Q1)
else if Q1 changes the selected setting and budget remains:
    relax again under Q1 -> S2
    confirm again on S2
else:
    report failed, inconclusive, or budget-exhausted outcome
```

Each repeated relaxation and confirmation receives new specification and
occurrence identities. The earlier structure remains immutable evidence. The
composition never mutates `Q0@S0` into `Q0@S1`, never treats `S1` as qualified
under changed `Q1`, and never interprets retry identity as a new scientific
coordinate.

## Lattice and reciprocal-sampling consistency

The existing grid assessment is rerun on each exact relaxed lattice. The final
stable pair records the full realized `PwDftKPointSamplingPolicy`, including
mesh, shifts, spatial-symmetry policy, and time-reversal policy. Equal integer
meshes on different structures remain distinct evidence and require fresh
confirmation.

Approximate lattice comparisons require prospectively declared units, metric,
tolerance, handedness, and non-finite-value behavior. Approximate equality does
not collapse exact structure records or erase predecessor lineage.

## Parent handoff

A terminal accepted pair identifies the exact structure and final numerical
setting but does not itself identify an executable parent state. A parent handoff
additionally requires the exact parent specification, prepared input,
occurrence, normalized evidence, and closed saved-state artifact inventory.

The confirmation occurrence cannot satisfy the parent role in this architecture.
After stable-pair acceptance, the composition requests a new parent SCF
occurrence so the five-occurrence downstream route begins only then. A future
reuse design would require separate review of identity, role closure, topology,
and authority. No result grants execution authority.

## Outcomes and budgets

Mechanical completion, criterion satisfaction, workflow acceptance, and
scientific validation are separate outcomes. The composition reports explicit
requirements or terminal outcomes such as accepted, failed, inconclusive, and
budget exhausted, with exact reasons and source identities.

Budgets bound coordinates, feedback iterations, and occurrences; they are not
scientific tolerances. Reaching a budget does not make the largest cutoff,
densest mesh, or latest structure converged.

Software tests use synthetic observations, retained evidence, or fake
executables in the owning outward layer. Passing them does not establish
numerical convergence for silicon or another material.
