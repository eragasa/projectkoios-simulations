# Calculator-neutral defect energetics numerical contract

## Purpose

This document separates numerical comparability from scientific acceptance.
The calculations must first be represented with enough exact information to
show what was compared. Passing these checks does not establish that the chosen
model, cell sizes, or thresholds are scientifically adequate.

## Energies used in comparisons

Formation and relaxation-energy arithmetic uses separately completed final
single-point energy observations on exact stored geometries. It does not use:

- an intermediate ionic step;
- the last printed value from an unconverged relaxation;
- energies parsed from different semantic stages without qualification; or
- energies from different methods without an explicit compatibility
  qualification.

The ideal, ion-only, and fully relaxed geometries each receive a final energy
evaluation under the same qualified method. This removes differences caused
solely by the relaxation algorithms' stopping and reporting behavior from the
intended energy comparison.

## Common-model checks

Before subtraction, the compatibility result records and compares:

- energy method and model identity;
- exact model parameters and external parameter-file identities;
- particle counts and state variables relevant to that method;
- implementation and observed version;
- exact prepared input identities;
- energy units and normalization; and
- completion and convergence observations defined by that method.

Exact equality is not required for fields that must differ physically, such as
structure identity. Every permitted difference must be named by the
qualification rather than ignored. Method-specific rules remain outside this
package. For example, the plane-wave DFT workflow checks
exchange-correlation, pseudopotentials, electron count, spin, cutoff, k-point
sampling, calculator inputs, and SCF convergence.

## Method-specific sampling

A changed fully relaxed cell may require a changed numerical sampling scheme.
The generic defect package does not prescribe how a method samples reciprocal
space, real space, configurations, or trajectories. The method-specific
qualification must retain the actual sampling parameters and the study rule
that selected them.

For the current plane-wave DFT workflow, a changed reciprocal lattice means that
an equal integer k-point tuple is not necessarily an equal reciprocal-space
sampling density. That workflow applies the Monkhorst–Pack and convergence
requirements recorded in its own `numeric.md` [1].

## Relaxation invariants

For ion-only relaxation:

- the output lattice must equal the exact normalized starting lattice;
- atomic species and count must remain unchanged;
- only positions may change; and
- pressure controls are absent.

For full relaxation:

- atomic species and count remain unchanged;
- positions and lattice may change;
- target pressure and tolerance are explicit; and
- final stress and cell-convergence observations are retained when available.

The full relaxation is initialized from the ion-only result. This provenance
does not prove that either relaxation found the global minimum. Distinct local
minima remain a possible explanation for an unexpected energy ordering.

## Difference and uncertainty reporting

The result stores each source energy and the derived differences at full retained
precision. Presentation rounding is separate. No absolute-value operation or
zero clamp is applied to a negative relaxation term.

A study-level numerical policy should declare an error budget that considers at
least:

- SCF energy tolerance;
- relaxation force and pressure tolerances;
- cutoff convergence;
- k-point convergence;
- finite-size change between adjacent supercells; and
- reproducibility of the selected local minimum.

Agreement between methods or implementations cannot be inferred from matching
labels. Broad solid-state DFT comparisons provide one concrete demonstration of
why complete calculation settings and reproducibility evidence matter [2].

## Size-series ordering

A size series is ordered by an exact structure derivation, transformation, and
atom count rather than by filename or label. The mechanical result reports
adjacent changes and, when declared, differences from a selected reference
size. It does not prescribe a particular set of sizes, fit an asymptotic law,
or declare convergence unless the workflow policy explicitly requests and
qualifies that operation.

## References

1. H. J. Monkhorst and J. D. Pack, “Special points for Brillouin-zone
   integrations,” *Physical Review B* **13**, 5188–5192 (1976),
   [doi:10.1103/PhysRevB.13.5188](https://doi.org/10.1103/PhysRevB.13.5188).
2. K. Lejaeghere *et al.*, “Reproducibility in density functional theory
   calculations of solids,” *Science* **351**, aad3000 (2016),
   [doi:10.1126/science.aad3000](https://doi.org/10.1126/science.aad3000).
