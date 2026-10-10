# Calculator-neutral defect energetics scientific basis

## Scope

This document records the scientific meaning assigned to the neutral defect
quantities in this package. It does not claim that a particular structure,
supercell size, energy method, model parameters, or numerical threshold is
scientifically adequate. Those claims require calculation evidence and an
explicit study-level acceptance policy.

## Formation energy

The package uses the standard chemical-potential construction for defect
formation energies described in the point-defect literature [1, 2]. For a
neutral defect with atom-count changes `delta_n[i]`, where additions are
positive and removals are negative,

```text
E_formation = E_defect - E_pristine - sum(delta_n[i] * mu[i]).
```

For substitutional phosphorus or boron on a silicon site,

```text
delta_n[Si] = -1
delta_n[X]  = +1

E_formation = E(Si_(N-1)X) - E(Si_N) + mu_Si - mu_X.
```

The defect and pristine energies must come from matched calculations. The
chemical potentials must come from compatible calculations of explicit
reference phases. An external phase database may select a phase, but an energy
from that database is not inserted into an expression using energies from a
different method.

The initial formation-energy contract is neutral only. Charged-defect formation
requires a separately reviewed particle-reservoir and correction-term contract.
Electronic-structure details such as electron-count changes, band edges,
electrostatic alignment, and periodic-charge corrections belong to the
method-specific workflow that supplies qualified evidence, not to the generic
neutral equation.

## Three defect geometries

Each defect has three separately identified structures:

1. **Ideal host geometry.** The defect has the exact host-supercell lattice and
   host positions. Only the declared site occupancy changes.
2. **Ion-only relaxed geometry.** Atomic positions relax while the host lattice
   remains fixed.
3. **Fully relaxed geometry.** Atomic positions and cell degrees of freedom
   relax under declared pressure controls.

The second and third structures are observations from separate relaxation
specifications. Neither can be inferred from the ideal defect delta.

## Operational strain-energy definition

At zero external pressure, compatible final single-point energies define:

```text
E_ionic = E_ideal - E_ion_only
E_strain = E_ion_only - E_fully_relaxed
E_total = E_ideal - E_fully_relaxed.
```

`E_strain` is the energy stored by constraining the relaxed defect to the host
cell, measured by the energy released when cell degrees of freedom are added.
This is an operational periodic-supercell quantity. It is not automatically an
isolated-defect elastic energy, elastic dipole, formation volume, or continuum
strain-field energy. Connecting it to those quantities requires additional
stress, volume, boundary-condition, and finite-size analysis such as the
elastic-defect framework reviewed by Clouet, Varvenne, and Jourdan [3].

A negative observed value is retained. It can indicate numerical uncertainty,
different local minima, incompatible final-SCF settings, or a failed
relaxation; it must not be silently replaced by zero.

At nonzero pressure, variable-cell relaxation minimizes a pressure-dependent
thermodynamic potential. The first contract therefore rejects an unqualified
total-energy strain comparison at nonzero pressure. A later enthalpy contract
must state the pressure, volume convention, and compatible quantity explicitly.

## Finite supercells

Periodic supercells make defect images interact. Formation energy, relaxation
energy, local geometry, and cell response may therefore vary with cell size.
The 64-, 216-, and 512-atom series is evidence for assessing that dependence;
it is not proof of convergence by construction. Finite-size scaling has also
been demonstrated for neutral native defects [4].

No universal threshold follows from these references. The workflow must state
the observable, units, threshold, stable window, and treatment of uncertainty.

## References

1. C. Freysoldt, B. Grabowski, T. Hickel, J. Neugebauer, G. Kresse,
   A. Janotti, and C. G. Van de Walle, “First-principles calculations for point
   defects in solids,” *Reviews of Modern Physics* **86**, 253–305 (2014),
   [doi:10.1103/RevModPhys.86.253](https://doi.org/10.1103/RevModPhys.86.253).
2. S. B. Zhang and J. E. Northrup, “Chemical potential dependence of defect
   formation energies in GaAs: Application to Ga self-diffusion,” *Physical
   Review Letters* **67**, 2339–2342 (1991),
   [doi:10.1103/PhysRevLett.67.2339](https://doi.org/10.1103/PhysRevLett.67.2339).
3. E. Clouet, C. Varvenne, and T. Jourdan, “Elastic modeling of point-defects
   and their interaction,” *Computational Materials Science* **147**, 49–63
   (2018),
   [doi:10.1016/j.commatsci.2018.01.053](https://doi.org/10.1016/j.commatsci.2018.01.053).
4. C. W. M. Castleton and S. Mirbt, “Finite-size scaling as a cure for
   supercell approximation errors in calculations of neutral native defects in
   InP,” *Physical Review B* **70**, 195202 (2004),
   [doi:10.1103/PhysRevB.70.195202](https://doi.org/10.1103/PhysRevB.70.195202).
