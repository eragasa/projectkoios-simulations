# Calculator-neutral defect energetics implementation rules

## Current module map

```text
src/python/projectkoios/simulations/defects/
  __init__.py
  chemical_potential.py
  compatibility.py
  energy.py
  formation_energy.py
  relaxation_energy.py
  size_convergence.py
```

- `chemical_potential.py` represents local elemental reference energies.
- `compatibility.py` represents an explicit qualification that names compared
  fields, permitted differences, limitations, and exact evidence identities.
- `energy.py` defines `DefectEnergyRole`, `DefectEnergyEvidence`, and exact
  method/model/evidence content references without importing DFT types.
- `formation_energy.py` owns atom-count terms, the sign convention, request,
  action, and immutable result.
- `relaxation_energy.py` compares ideal, ion-only, and fully relaxed defect
  energies using qualified final single-point evidence at zero pressure.
- `size_convergence.py` owns composition-matched mechanical differences, but no
  scientific acceptance policy.

Public records and actions remain frozen, slotted dataclasses. No provider,
workflow, pymatgen, or Materials Project type may cross this package boundary.

## Evidence requirements

Every energy term must be a frozen, slotted `DefectEnergyEvidence` record with:

- semantic role;
- finite scalar energy and explicit unit;
- exact structure content reference;
- exact method/model identity;
- exact source-evidence content reference;
- compatibility-qualification identity; and
- normalization and sign qualification.

Content references carry stable ID, representation, schema version, byte size,
and SHA-256 without importing the owning DFT, integration, or evidence package.
Inputs must name the exact role of each record:

- defect supercell;
- pristine supercell;
- host-element reference; and
- each added or removed species reference.

The action must reject duplicate roles, missing terms, element mismatches,
unsupported charge states, non-finite energies, ambiguous units, incomplete
energy observations, and evidence that has not passed the declared
compatibility qualification. Method-specific workflows may impose additional
requirements before constructing that qualification.

## Atom-count convention

Let `delta_n[element]` be the number of atoms added to the pristine cell to form
the defect cell; removals are negative. The neutral expression is:

```text
E_formation = E_defect - E_pristine - sum(delta_n[i] * mu[i])
```

For substitutional phosphorus or boron in silicon:

```text
delta_n[Si] = -1
delta_n[P or B] = +1
```

which yields `E_defect - E_pristine + mu_Si - mu_X`. The implementation stores
the convention and terms in the result so the sign cannot be reconstructed
from prose.

## Compatibility policy

A compatibility qualification identifies the energy method and every field
required to establish a common energy convention. Those fields depend on the
method: a plane-wave DFT workflow checks exchange-correlation, spin,
pseudopotentials, electron count, cutoffs, sampling, calculator identity, and
version, while another atomistic model has different requirements.

The neutral defect package does not pretend those method-specific fields are
universal. It requires the qualification to enumerate compared fields,
permitted differences, and unresolved limitations. Structure and sampling may
differ between roles only when the qualification says why that difference is
allowed.

A compatibility result is mechanical evidence. It must not be named or
documented as scientific acceptance, numerical validation, or universal
transferability.

## Relaxation and cell-strain energy

One relaxation-energy input binds three exact structures of identical
composition and charge:

- ideal host-geometry defect;
- ion-only relaxed defect from `ATOMIC_POSITIONS`; and
- fully relaxed defect from `ATOMIC_POSITIONS_AND_CELL`.

The action requires separate qualified final single-point energy evidence for
all geometries. It verifies that the ideal and ion-only cells retain the host
lattice and that the full cell descends from the same defect declaration. It
must not compare intermediate optimizer-step energies from two relaxation
trajectories. The method-specific qualification establishes the common model
and energy normalization.

At zero declared external pressure it reports:

```text
ionic_relaxation_energy = E_ideal - E_ion_only
cell_strain_energy      = E_ion_only - E_fully_relaxed
total_relaxation_energy = E_ideal - E_fully_relaxed
```

The result records the sign convention and checks the additive identity without
assuming any term is positive. At nonzero pressure, the total-energy form is
rejected until a compatible enthalpy contract is represented.

## Size convergence

A size-convergence series binds each formation-energy and relaxation-energy
result to the exact pristine structure derivation or supercell transformation.
Ordering is by the declared transformation and atom count, not filename or
display label. The mechanical action may report adjacent differences and
differences from a selected reference size.

The action does not choose a threshold or declare convergence. Those decisions
belong to `projectkoios.simulations.workflows.pw_dft_defect_formation`.

## Charged defects

The first formation-energy implementation supports `charge_state == 0` only.
Nonzero values fail before formation-energy arithmetic. A future generic charged
contract must represent the relevant particle reservoir and every required
correction term without assuming that all energy methods use DFT band edges or
one electrostatic correction model.

The plane-wave DFT workflow additionally records `delta_n_electrons`, requires
`charge_state == -delta_n_electrons`, and will eventually need Fermi-level,
band-edge, potential-alignment, compensating-background, dielectric, and
image-charge correction provenance. Those are method-specific bindings around
the generic formation-energy expression, not fields of
`projectkoios.simulations.defects`.

## Required verification

Tests must cover the sign convention, multiple added and removed species,
missing chemical potentials, mismatched evidence roles, exact-model
compatibility, allowed sampling differences, non-finite values, units,
incomplete observations, neutral-charge enforcement, method-qualification
requirements, charged-formation-energy rejection, deterministic ordering, and
size-difference arithmetic. Method-specific tests separately cover electron
count, spin, and input-model compatibility. Tests use synthetic immutable
evidence only and
must not invoke integrations or calculators.
