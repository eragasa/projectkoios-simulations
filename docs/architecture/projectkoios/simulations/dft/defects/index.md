# Plane-wave DFT binding for defect energetics

## Status

An initial protected-core implementation now binds structural charge to
`delta_n_electrons`, enforces neutral substitutional Si:P and Si:B doublets,
qualifies
converged final SCFs with exact pseudopotentials and prepared-input charge/spin
mappings, and delegates neutral formation-energy arithmetic to
[`projectkoios.simulations.defects`](../../defects/index.md). Complete cutoff,
k-point, occupation, and exchange-correlation comparison records remain to be
added before study evidence is complete.

## Purpose

`projectkoios.simulations.dft.defects` translates exact plane-wave DFT
specifications and normalized DFT evidence into the compatibility and energy
terms consumed by the method-neutral defect package. It owns DFT-specific
meaning, including:

- electron-count and defect-charge consistency;
- exchange-correlation and pseudopotential compatibility;
- spin and occupation compatibility;
- cutoff and Brillouin-zone sampling qualification;
- final-SCF energy qualification; and
- future charged-periodic-cell correction evidence.

Its DFT-specific formation-energy action validates and binds DFT evidence, then
delegates arithmetic to `projectkoios.simulations.defects.formation_energy`. It
does not duplicate the generic formation-energy, relaxation-energy, or
size-difference equations.

## Charge and electron count

Every plane-wave DFT specification records an integer
`delta_n_electrons` relative to the neutral electron count for the same nuclei
and exact pseudopotentials. Positive values add electrons and negative values
remove them. When a calculation represents a declared defect charge, the
binding requires:

```text
charge_state == -delta_n_electrons
```

A neutral substitution may change the neutral valence count through its changed
species while keeping `delta_n_electrons == 0`. For example, the phosphorus
donor electron is part of neutral Si:P rather than an extra charged-cell
electron.

## Spin

The binding retains spin mode, intended spin-channel electron difference,
constraint policy, initial moments, and normalized observed magnetization when
available. It does not infer spin intent from a calculator default.

The current neutral Si:P and Si:B workflow requires collinear spin-polarized
doublets. That is a workflow scientific requirement checked through this DFT
binding, not
a universal property of every defect accepted by
`projectkoios.simulations.defects`.

## Generic result boundary

After qualification, this package produces method-neutral terms and a complete
compatibility result. The generic package then performs arithmetic such as:

```text
E_formation = E_defect - E_pristine - sum(delta_n[i] * mu[i])
E_strain = E_ion_only - E_fully_relaxed
```

The generic result retains the DFT qualification identity and source evidence,
but it does not import a QE or VASP type.

## Non-goals

This package does not render QE or VASP input, parse their files, select a
calculator, authorize execution, own workflow policy, or claim scientific
acceptance. Outward integrations create inputs and normalize observations;
workflow composition decides which qualified calculations belong in a study.

See [`implementation.md`](implementation.md) for planned records,
[`schematics.md`](schematics.md) for the two-layer flow,
[`scientific.md`](scientific.md) for cited DFT-specific meaning, and
[`numeric.md`](numeric.md) for numerical comparability requirements.
