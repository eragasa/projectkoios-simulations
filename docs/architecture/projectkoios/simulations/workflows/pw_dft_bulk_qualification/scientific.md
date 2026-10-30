# Plane-wave DFT bulk qualification scientific boundary

This document constrains a planned, unimplemented capability. It does not
qualify a material, reserve a public API, or provide execution authority.

## Qualification is structure scoped

Plane-wave basis and reciprocal-sampling convergence are properties of an exact
scientific model evaluated on an exact structure. A convergence result from a
provisional seed geometry can guide a later relaxation, but it is not a
structure-independent certificate. Relaxation changes direct and reciprocal
lattices and may alter the energy sensitivity to basis and sampling choices.

The planned workflow therefore records `Q0@S0` as provisional, mechanically
qualifies a new structure `S1`, and performs a fresh numerical confirmation
`Q1@S1`. It accepts only a correlated structure/setting pair. The workflow does
not mutate the identity or scope of earlier evidence.

## Existing convergence and neutral cutoff meaning

The existing joint grid varies wavefunction cutoff and cubic k-point density.
A separate neutral cutoff realization declares the physical wavefunction and
density/potential plane-wave basis settings without naming provider controls.
First-party adapter evidence proves how each exact native input realizes that
neutral setting. The stable-pair handoff references the neutral realization,
not QE `ecutrho` or `charge_density_cutoff_ratio`.

This addition does not replace the existing recipe, assessor, or controller.
The reusable workflow does not prescribe a universal multiple, cutoff series,
energy threshold, or pseudopotential recommendation. Independently varying the
density/potential cutoff is outside this route and requires separate review.

## Reciprocal sampling after relaxation

A changed direct lattice has a changed reciprocal lattice. This architecture
therefore reruns the existing grid-convergence assessment on the exact relaxed
structure. The accepted full `PwDftKPointSamplingPolicy` is recorded in the
stable pair. No new reciprocal-density rule or generalized coordinate is needed
for the first symmetry-preserving cubic route.

## Zero-pressure structure meaning

A variable-cell optimizer searches only the degrees of freedom, starting basin,
electronic state, and mechanical condition declared by its specification.
Provider completion and an optimizer convergence marker do not establish all of
the following:

- that the normalized final cell is valid and respects the allowed cell mode;
- that maximum force satisfies the campaign criterion;
- that the residual from the declared zero-pressure target satisfies the
  campaign criterion;
- that all retained artifacts and normalized quantities are mutually
  consistent;
- that the result is a global energy minimum; or
- that the structure is experimentally or scientifically validated.

The reusable assessment reports these facts separately. The accepted
variable-cell qualification contract requires finite maximum force, finite
scalar pressure, and complete finite normalized stress and recomputes the force
and pressure criteria from those observations. For pristine bulk silicon,
volume-only versus unrestricted or another cell mode remains an exact
consumer-owned choice; the workflow does not infer it from a provider label.

## Feedback after changed settings

If confirmation on `S1` requires a tighter or otherwise changed setting `Q1`, a
single high-resolution energy evaluation on `S1` is not a structural
qualification under `Q1`. The force and stress surface may have changed. The
workflow therefore requests a new relaxation under `Q1`, then confirms the
numerical setting on the resulting exact structure. A bounded feedback policy
prevents this scientific dependency from becoming an unbounded runtime loop.

The resulting structures may be close within a reporting tolerance. They still
have different exact identities unless an explicit canonical identity contract
proves otherwise. Approximate geometric agreement must not rewrite lineage.

## Final parent boundary

The accepted pair supplies exact structure and numerical-setting requirements
for a final parent SCF. Relaxation's last electronic state is optimizer evidence
and is not silently promoted to a reusable parent saved state. The confirmation
SCF also remains predecessor evidence rather than the route parent. After pair
acceptance, a new separately authorized parent occurrence begins the
five-occurrence downstream route. Reuse would require a future separate review
and is not implied by matching settings or available saved-state files.

The subsequent Wannier route keeps parent SCF, uniform-grid NSCF, Wannier90
preprocessing, interface generation, and localization as distinct scientific
operations and distinct calculator occurrences.

## Acceptance limits

This workflow may establish that declared identities, evidence, dimensions,
orders, normalized residuals, and prospective numerical criteria are
consistent. It does not establish:

- transferability of a pseudopotential or electronic model;
- global structural stability or dynamical stability;
- a universal cutoff, k-point density, force, or pressure threshold;
- adequacy for every downstream observable;
- agreement with experiment; or
- publication-quality scientific validation.

A consuming project owns threshold selection, validation, evidence promotion,
and publication decisions. Budget exhaustion or missing evidence remains
inconclusive rather than being relabeled as convergence.
