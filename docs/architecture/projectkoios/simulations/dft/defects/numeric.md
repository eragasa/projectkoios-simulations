# Plane-wave DFT defect binding numerical contract

## Purpose

This document defines the DFT-specific checks performed before total energies
become qualified inputs to `projectkoios.simulations.defects`. Passing these
checks establishes traceable numerical comparability under a declared policy;
it does not establish scientific validation.

## Final energies

Every ideal, ion-only, and fully relaxed geometry receives a separate final SCF.
The binding rejects an intermediate ionic-step energy, an unconverged last
relaxation step, or an energy not correlated with the exact stored geometry and
prepared calculator inputs.

The final SCF records:

- exact structure and simulation identities;
- exact rendered calculator inputs and required external inputs;
- total energy and units;
- SCF completion and convergence observations;
- electronic charge and spin evidence; and
- native artifact identities and normalization provenance.

## Common DFT model

Before subtraction, the DFT compatibility result compares:

- exchange-correlation model;
- exact pseudopotential records for every shared element;
- `delta_n_electrons`, defect charge, and their sign invariant;
- compensating-background and charged-cell treatment when relevant;
- spin mode, intended spin-channel difference, constraints, and initial moments;
- occupations and smearing;
- wavefunction and charge-density cutoffs;
- k-point mesh and mesh-selection policy;
- calculator integration and observed version; and
- final-SCF convergence.

Permitted differences are explicit. A missing field is unavailable evidence,
not an assumed match.

## Spin-polarized Si:P and Si:B

Every neutral Si:P and Si:B geometry and final SCF in one series uses a
collinear spin-polarized doublet specification. The prepared input must show how the
calculator represents the spin-channel difference or initialization. The
normalized result retains observed total magnetization or spin populations when
available.

A non-spin-polarized energy, a different spin constraint, or a calculation that
settles into an incompatible spin state is rejected from the series or retained
as a separately identified comparison.

## Brillouin-zone sampling

A fully relaxed cell may have a changed reciprocal lattice. Equal integer
k-point tuples therefore do not necessarily mean equal reciprocal-space
sampling density. The policy records the actual regular special-point mesh and
its selection rule, following the Monkhorst–Pack construction [1]. It either:

1. retains one mesh with explicit convergence justification; or
2. derives each mesh from one declared reciprocal-space density rule.

No mesh is silently copied because two calculations share a human-readable
label.

## Error and convergence evidence

The DFT qualification retains the numerical evidence relevant to each energy
difference, including:

- SCF tolerance;
- ionic force and variable-cell pressure tolerances;
- cutoff convergence;
- k-point convergence;
- finite-size change;
- spin-state consistency; and
- evidence of different local minima.

Negative relaxation-energy terms are preserved and investigated rather than
clamped. Presentation rounding does not alter stored energies or derived
results.

## References

1. H. J. Monkhorst and J. D. Pack, “Special points for Brillouin-zone
   integrations,” *Physical Review B* **13**, 5188–5192 (1976),
   [doi:10.1103/PhysRevB.13.5188](https://doi.org/10.1103/PhysRevB.13.5188).
2. K. Lejaeghere *et al.*, “Reproducibility in density functional theory
   calculations of solids,” *Science* **351**, aad3000 (2016),
   [doi:10.1126/science.aad3000](https://doi.org/10.1126/science.aad3000).
