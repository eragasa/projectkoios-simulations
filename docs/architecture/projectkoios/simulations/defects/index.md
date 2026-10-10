# Calculator-neutral defect formation and relaxation energetics

## Status

An initial protected-core implementation now provides method-neutral exact
energy evidence, elemental
chemical potentials, explicit compatibility records, neutral formation-energy
arithmetic, three-stage relaxation-energy arithmetic, and matched size
convergence. Charged formation-energy corrections remain intentionally
unimplemented pending complete charged-defect contracts.

## Purpose

`projectkoios.simulations.defects` defines pure operations for deriving
defect formation, relaxation, and finite-size observations from exact,
compatible `DefectEnergyEvidence` records. Each record carries an energy, unit,
role, structure, method/model identity, source-evidence identity, and
compatibility qualification without importing a DFT type. The equations apply
independently of whether those energies come from plane-wave DFT, another
electronic-structure method, or a validated atomistic model.

The package will not construct structures, choose an energy method or
calculator, execute a calculation, select an elemental phase from an external
database, or decide whether a study is scientifically acceptable.

## Separation from structural defects

The structure layer answers:

```text
What atoms and lattice define this ideal bulk or defect cell?
```

This energetics layer answers:

```text
Given explicitly qualified local calculation evidence, what energy expression
and mechanical size-convergence observations follow?
```

`UnitCellDefectDelta` remains in `projectkoios.simulations.structure.defect`.
No vacancy, interstitial, substitution, or complex class hierarchy is added to
the energetics package.

## Chemical potentials

A chemical potential used in a defect-energy expression must come from a
compatible calculation of an explicitly identified reference phase. An
external database may identify that phase and provide its structure, but its
energy is not mixed directly with energies from a different method or model.

Each local chemical-potential record therefore references:

- the selected elemental phase structure record;
- the local simulation specification record;
- qualifying local evidence;
- the element and atoms per reference formula or cell; and
- the resulting local energy per atom.

## Formation-energy expressions

For a neutral substitution replacing one silicon atom with element `X`, the
initial supported expression is:

```text
E_f(X_Si^0) = E(Si_(N-1)X) - E(Si_N) + mu_Si - mu_X
```

The atom-count delta and sign convention must be explicit data, not inferred
from display labels such as `Si:P`, `Si:B`, or Kröger–Vink notation.

The generic formation-energy request retains `charge_state`, but the initial
action supports neutral defects only. Charged-defect formation energies require
additional electron-reservoir and method-specific correction terms. Until those
contracts exist, the action rejects nonzero charge rather than silently omitting
terms.

An electronic-structure specification may additionally record
`delta_n_electrons`. The plane-wave DFT workflow requires
`charge_state == -delta_n_electrons`, but that calculation-specific field is not
part of the method-neutral formation-energy equation.

## Defect relaxation and strain energy

Each defect study distinguishes three exact geometries:

1. the ideal defect at the host-supercell lattice parameters and host atomic
   positions, changing only the declared species/removal/addition;
2. an ion-only relaxed defect with the host lattice fixed; and
3. a fully relaxed defect in which ions and cell may relax under declared
   pressure controls.

Each relaxed geometry receives a separate final single-point energy evaluation
under one qualified energy model. Strain comparisons use those final energy
observations, not intermediate relaxation-step energies. The current
plane-wave DFT workflow realizes a final energy evaluation as a final SCF. At
zero external pressure, the
stored cell-strain relaxation energy is declared with the sign convention:

```text
E_strain = E_final(ion-only relaxed)
         - E_final(fully relaxed)
```

A positive value is the energy released when cell degrees of freedom are added.
The signed reverse difference may also be reported, but it must not share the
same name. Negative values are retained and qualified as possible numerical
noise, incomparable settings, or different local minima rather than silently
clamped.

The ideal-to-ion-only difference separately measures ionic relaxation energy;
the ideal-to-fully-relaxed difference measures total relaxation energy. For
nonzero external pressure, comparison requires a separately declared common
thermodynamic potential such as enthalpy rather than an unqualified total-energy
difference.

## Compatibility and acceptance

A pure qualification operation determines whether the defect, pristine,
elemental-reference, ion-only, and fully relaxed evidence is mechanically
eligible for one derivation. Its result records compared fields and permitted
differences. Qualification does not claim scientific validation.

Size-convergence records may calculate ordered differences across 64-, 216-,
and 512-atom cells. Thresholds, stability windows, exclusions, strain-energy
interpretation, and acceptance remain workflow-owned policy.

See [`implementation.md`](implementation.md) for planned records and validation,
[`schematics.md`](schematics.md) for the energy and dependency flows,
[`scientific.md`](scientific.md) for the physical definitions and cited basis,
and [`numeric.md`](numeric.md) for numerical comparability and error controls.
