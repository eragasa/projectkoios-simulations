# Plane-wave DFT relaxation scientific semantics

## Degrees of freedom

An ionic relaxation searches atomic positions under a fixed periodic cell. A
variable-cell relaxation also searches declared cell degrees of freedom under a
pressure/stress condition. These are different scientific specifications and
produce separately identified structures.

“Fully relaxed” must not be inferred from a provider's `relax` or `vc-relax`
label alone. The specification states which cell components may change, target
pressure, force and pressure criteria, spin state, and symmetry constraints.
Variable-cell methods explicitly couple structural and cell degrees of freedom
under a chosen mechanical condition [1].

## Local minima

A converged optimizer reports a stationary point reached from one starting
geometry and electronic state. It does not prove that the structure is the
global minimum. Defects may exhibit symmetry breaking, metastable structures,
or spin-dependent geometries [2]. Initial displacement, symmetry, and spin
policies therefore belong to the exact specification and evidence.

The workflow decides whether several initializations are required and how their
results are compared. The protected relaxation result reports each completed
calculation without selecting the scientifically preferred minimum.

## Fixed-cell defect relaxation

For the ion-only stage, the host-supercell lattice remains fixed while defect
and host atoms may move. This isolates internal coordinate relaxation under the
chosen periodic boundary condition. It does not remove homogeneous strain that
could be released by changing the cell.

## Variable-cell defect relaxation

For the ion-and-cell stage, allowed lattice degrees of freedom may release
additional periodic-cell constraint energy. Interpretation depends on whether
volume, shape, or all lattice vectors were allowed and on the target external
pressure. The architecture therefore requires an explicit mode rather than a
single ambiguous “cell relaxation” boolean.

## Energies

Relaxation trajectory energies are optimizer evidence, not the final comparable
energy used automatically in defect formation or strain arithmetic. Each
published geometry receives a separate final SCF under the qualified energy
model. This distinguishes geometry optimization stopping behavior from the
energy comparison.

At nonzero pressure, a variable-cell calculation is associated with a
pressure-dependent thermodynamic potential. A total-energy difference must not
be called strain energy without an explicit common-potential contract.

## Acceptance boundary

Provider completion, optimizer convergence, numerical qualification, workflow
acceptance, and scientific validation remain separate. A result may be useful
evidence even when it fails a later force, pressure, spin, or size-convergence
policy.

## References

1. R. M. Wentzcovitch, “Invariant molecular-dynamics approach to structural
   phase transitions,” *Physical Review B* **44**, 2358–2361 (1991),
   [doi:10.1103/PhysRevB.44.2358](https://doi.org/10.1103/PhysRevB.44.2358).
2. C. Freysoldt *et al.*, “First-principles calculations for point defects in
   solids,” *Reviews of Modern Physics* **86**, 253–305 (2014),
   [doi:10.1103/RevModPhys.86.253](https://doi.org/10.1103/RevModPhys.86.253).
