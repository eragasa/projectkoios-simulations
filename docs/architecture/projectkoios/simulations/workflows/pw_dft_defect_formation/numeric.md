# Plane-wave DFT defect-formation workflow numerical policy

## Purpose

The workflow numerical policy turns qualified observations into explicit
accept, extend, inconclusive, or budget-exhausted decisions. It does not hide
missing evidence behind default values and does not treat the presence of three
supercell sizes as convergence by itself.

The underlying arithmetic and comparability requirements are defined in the
[defect numerical contract](../../defects/numeric.md).

## Complete size-role matrix

For each impurity and each 64-, 216-, and 512-atom host size, the workflow
requires exact roles for:

- pristine host final SCF;
- ideal, `<100>`, and `<111>` defect starts;
- fixed-host ion relaxation and final SCF for every start;
- lowest-compatible-observed-basin selection; and
- residual stress for the selected fixed-host result.

Optional full-cell diagnostics remain separate roles. Formation energy
additionally requires compatible local Si and impurity chemical-potential
evidence. Every neutral Si:P and Si:B role requires an exact spin-polarized
doublet specification, disabled spatial and time-reversal reductions, and
prepared calculator inputs that realize them. A missing role produces a typed
requirement or an inconclusive outcome,
never an assumed zero or a reused unlike calculation.

## Plane-wave DFT compatibility

Before constructing the generic energy-compatibility qualification, this
workflow compares:

- exchange-correlation model;
- exact pseudopotential identities;
- `delta_n_electrons`, charge sign, and compensating-background treatment;
- spin mode, intended spin-channel difference, constraints, and initial moments;
- occupations and smearing;
- wavefunction and charge-density cutoffs;
- k-point meshes and the rule that selected them;
- rendered calculator input identities;
- calculator implementation and version; and
- SCF completion and convergence observations.

A changed fully relaxed lattice has a changed reciprocal lattice. The workflow
therefore does not assume that the same integer k-point tuple represents the
same sampling density. It records the actual Monkhorst–Pack mesh [3] and either
retains it under an explicit convergence justification or derives it from one
declared reciprocal-space density rule.

## Independent acceptance dimensions

The policy assesses at least two ordered series independently:

```text
formation_energy[size]
fixed_host_residual_stress[size]
```

It may also assess ionic relaxation energies and optional full-cell release
energies. Each series declares
its own units, comparison metric, threshold, stable window, maximum additional
sizes, and missing-evidence behavior. Formation-energy stability cannot stand
in for strain-energy stability or vice versa.

## Adjacent-size evidence

For ordered sizes `N_1 < N_2 < N_3`, the mechanical observations include:

```text
Delta_12 = E(N_2) - E(N_1)
Delta_23 = E(N_3) - E(N_2)
```

An acceptance policy must state whether it uses signed change, absolute change,
a reference-to-largest difference, or a fitted model. The initial architecture
does not prescribe a universal electron-volt threshold. The point-defect
literature demonstrates that finite-size behavior depends on defect charge,
material response, boundary conditions, and correction model [1, 2].

## Relaxation checks before energy comparison

Before selecting a defect energy, the workflow requires:

- completed fixed-host relaxation observations from all three declared starts;
- exact provenance from the same defect declaration;
- fixed-lattice verification for every result;
- compatible final-SCF settings, including identical doublet intent across all
  neutral Si:P or Si:B starts, disabled reductions, and converged observations;
- lowest-observed-basin selection from compatible final-SCF energies; and
- an explicit statement that optimizer convergence is not vibrational proof of
  a local or global minimum.

An optional full-cell comparison additionally requires pressure qualification
and a common zero-pressure total-energy convention.

Unexpected negative relaxation terms are reported with their evidence. They
produce an inconclusive or rejected qualification according to policy; they are
not clamped.

## Numerical budgets

A calculation budget and a scientific acceptance threshold are different. The
budget limits how many additional coordinates or sizes may be requested. Budget
exhaustion means the declared study stopped without the required stability; it
does not mean that the largest available supercell is converged.

Retries of one failed workflow occurrence do not create a new scientific size.
Adding a larger supercell creates a new specification and workflow occurrence.

## Reporting

A terminal study result retains:

- all source evidence identities;
- all rejected or missing roles;
- exact energy values and units;
- derived signed differences;
- policy version and thresholds;
- stable-window membership;
- budget use; and
- one explicit outcome for each assessed quantity.

Presentation rounding does not alter stored values or decisions.

## References

1. C. Freysoldt *et al.*, “First-principles calculations for point defects in
   solids,” *Reviews of Modern Physics* **86**, 253–305 (2014),
   [doi:10.1103/RevModPhys.86.253](https://doi.org/10.1103/RevModPhys.86.253).
2. C. W. M. Castleton and S. Mirbt, “Finite-size scaling as a cure for
   supercell approximation errors in calculations of neutral native defects in
   InP,” *Physical Review B* **70**, 195202 (2004),
   [doi:10.1103/PhysRevB.70.195202](https://doi.org/10.1103/PhysRevB.70.195202).
3. H. J. Monkhorst and J. D. Pack, “Special points for Brillouin-zone
   integrations,” *Physical Review B* **13**, 5188–5192 (1976),
   [doi:10.1103/PhysRevB.13.5188](https://doi.org/10.1103/PhysRevB.13.5188).
