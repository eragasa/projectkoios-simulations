# Plane-wave DFT defect binding implementation rules

## Current module map

```text
src/python/projectkoios/simulations/dft/defects/
  __init__.py
  binding.py
  charge.py
  compatibility.py
  formation_energy.py
```

- `binding.py` correlates an exact plane-wave DFT simulation, prepared inputs,
  normalized final-SCF observation, and method-neutral energy evidence.
- `charge.py` validates structural `charge_state`, `delta_n_electrons`, the exact
  derived cell, and neutral substitutional Si:P and Si:B doublets.
- `compatibility.py` currently compares method/model, qualification, and final
  SCF state and produces the method-neutral compatibility record.
- `formation_energy.py` validates the plane-wave DFT method and invokes the
  generic neutral formation-energy action.

The compatibility action explicitly records that cutoff, k-point, occupation,
calculator-version, exchange-correlation, and exact pseudopotential comparison
still require richer evidence fields. It does not overstate the initial record
as complete DFT compatibility.

The DFT module does not reimplement the equation. Arithmetic authority remains
`projectkoios.simulations.defects.formation_energy`; the DFT action supplies its
qualified inputs and preserves DFT-specific evidence in the correlated result.

## Allowed imports

The package may import:

- standard-library modules;
- protected structure, simulation-library, evidence, plane-wave DFT, and
  method-neutral defect contracts; and
- other protected-core modules that do not depend on workflows or integrations.

It must not import:

- `projectkoios.simulations.workflows`;
- QE, VASP, Materials Project, or another integration;
- pymatgen, mp-api, or calculator-native parser models;
- repository tools or examples; or
- live Workflow runtime objects.

## Binding record

A DFT defect binding identifies:

- the complete `UnitCellDefectDelta` and derived structure record;
- exact pristine and defect `SimulationRecord` values;
- `charge_state` and integer `delta_n_electrons`;
- complete spin and occupation intent;
- exact pseudopotentials and exchange-correlation model;
- exact prepared calculator-input records;
- normalized final-SCF evidence; and
- the role the energy has in one generic derivation.

The binding rejects a structure/specification mismatch, element mismatch,
charge/electron-count mismatch, missing spin declaration, or evidence that does
not identify the bound simulation and prepared inputs.

## Compatibility qualification

The DFT qualifier compares at least:

- exchange-correlation identity;
- exact pseudopotential records for shared elements;
- charge and electron-count conventions;
- spin mode, spin-channel difference, constraints, and initial moments;
- occupation and smearing treatment;
- wavefunction and charge-density cutoff controls;
- k-point mesh and mesh-selection rule;
- calculator integration and observed version;
- exact rendered input identities; and
- final-SCF completion and convergence observations.

Differences required by distinct cells, elements, or reference phases are
permitted only when the qualification policy names them. Its output enumerates
matches, permitted differences, failures, and unavailable evidence. It is a
mechanical eligibility result, not scientific acceptance.

## Neutral and charged boundaries

The first generic formation-energy action accepts neutral evidence only. This
DFT package may bind and retain a charged SCF or relaxation calculation, but it
must not construct a formation-energy qualification until all required
Fermi-level, band-edge, potential-alignment, background-charge, dielectric, and
finite-size correction records exist.

For every bound defect calculation:

```text
charge_state = -delta_n_electrons
```

The initial schema uses integral values. Fractional electronic charging would
require a separately reviewed scientific meaning and schema rather than a float
substitution.

## Required verification

Tests must cover neutral substitutions, positive and negative charge signs,
neutral valence changes, mismatched structural and electronic charge, missing
spin intent, neutral Si:P and Si:B doublet qualification, pseudopotential and
functional mismatch, cutoff and k-point differences, calculator/version
identity, missing
prepared inputs, unconverged final SCF, and conversion to method-neutral energy
terms. Tests use synthetic evidence and never execute a calculator.
