# Plane-wave DFT bulk qualification implementation rules

## Reuse-first package

The production package does not yet exist. It will compose existing public
`pw_dft_scf` and `pw_dft_relaxation` workflow contracts. Proposed module and
symbol names remain unreserved.

The current convergence recipe, coordinate, assessor, controller, k-point
policy, pseudopotential records/library, generic executor, and evidence records
remain unchanged. Two additive neutral prerequisites are required around them:
a provider-neutral coupled-cutoff realization and a typed structure-scoped grid
correlation that binds current observations/assessment to exact requests and
evidence.

## Minimal concepts

The package needs only:

- a declaration binding the exact seed structure, neutral coupled-cutoff
  realization, existing grid recipe/policy, existing relaxation
  specification/policy, confirmation rule, and budgets;
- a typed correlation binding each existing grid observation to its exact
  structure, projected request/specification, prepared input, occurrence,
  `SimulationEvidenceRecord`, normalized bytes, adapter mapping, and unchanged
  existing assessment;
- a pure zero-pressure assessment over an existing relaxation result;
- an iteration record correlating one accepted typed grid qualification, one
  existing relaxation result/publication, and one typed confirmation; and
- a terminal accepted structure/neutral-settings pair or explicit failed,
  inconclusive, or budget-exhausted outcome.

Records are frozen and slotted. They contain no provider object, executable,
authorization flag, queue state, lease, retry counter, or mutable runtime state.
For variable-cell qualification, the accepted zero-pressure contract requires
finite maximum force, finite scalar pressure, and complete finite normalized
stress and recomputes every threshold comparison from those observations.

## Existing convergence reuse

Both `Q0@S0` and `Q1@S1` use:

- `PwDftScfGridConvergenceRecipe`;
- `EnergyGridConvergenceAssessor`; and
- `PwDftScfConvergenceController`.

The current cubic mesh coordinate and wavefunction-cutoff series remain intact.
Existing observations and assessments are not themselves structure/evidence
scoped. The additive typed correlation supplies that scope and, after
validating every child identity, selects the highest tested mesh/cutoff corner
from an accepted correlation as the production coordinate.

The stable-pair handoff references a neutral physical wavefunction and
density/potential cutoff realization. QE `ecutwfc`, `ecutrho`, and
`charge_density_cutoff_ratio` remain provider projection details. First-party
adapter evidence proves that each exact QE input realizes the neutral setting;
no QE field enters the neutral handoff.

## Feedback composition

The composition derives one deterministic next scientific requirement or
terminal outcome. It:

1. accepts `Q0` only for exact `S0`;
2. requests existing relaxation under `Q0`;
3. assesses zero pressure from the existing result and publishes exact `S1`;
4. reruns the existing grid assessment at `S1`;
5. accepts `(S1, Q1)` when stable; or
6. requests re-relaxation under changed `Q1` and reconfirmation within budget.

It does not invoke a provider, schedule a job, infer authorization, or mutate
earlier evidence.

## Dependencies and boundaries

Production modules import only protected simulation contracts and public
provider-independent sibling workflow contracts. They do not import
integrations, adapters, repository tools, a consuming application, or Workflow
runtime implementations.

First-party `projectkoios.adapters` maps exact provider observations to neutral
facts, including native-to-neutral cutoff realization and pseudopotential
source/content evidence. `tools/pw_dft_bulk_qualification` owns provider
selection, operational configuration, local resource resolution, explicitly
authorized acquisition, invocation, and replay. External Workflow
infrastructure owns scheduling and persistence.

The existing neutral `PseudopotentialFile` and local
`PseudopotentialLibrary` are preserved. Outward ProjectKoios integrations,
adapters, and tools additionally own source/catalog metadata discovery,
authorized acquisition of absent bytes, hash/size authentication, and catalog
evidence. Neither documentation nor an ordinary workflow invocation authorizes
network acquisition.

## Verification

Calculator-free tests must establish:

- typed exact structure/request/input/occurrence/evidence binding for every
  observation;
- unchanged existing grid convergence behavior;
- neutral coupled-cutoff identity and exact QE adapter realization without QE
  fields in neutral records;
- zero-pressure force/pressure/stress assessment and missing-evidence behavior;
- fresh confirmation on the exact relaxed structure;
- re-relaxation after a changed accepted setting;
- bounded feedback and explicit exhaustion;
- stable-pair cardinality and canonical identity;
- separate occurrence authorization;
- pseudopotential catalog/authentication behavior with fake local providers and
  no unapproved network access; and
- absence of provider imports or execution authority in neutral modules.

Passing tests establishes software-contract behavior only, not material
convergence or scientific validity.
