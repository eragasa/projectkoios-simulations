# VASP SCF calculator-input translation

`VASP_SCF_INTEGRATION_ID` identifies the backend. `VaspScfInputProjector`
composes maintained INCAR, KPOINTS, POSCAR, and calculation renderers. The
existing Python name uses “projection”; architecturally this is translation into
exact VASP input files.

## Defect extension status

The current translator derives `ISPIN`, `NUPDOWN`, and `MAGMOM` from neutral
spin intent and derives charged `NELECT` from exact pseudopotential valence
metadata plus `delta_n_electrons`. Calculator configuration no longer owns an
independent spin-polarization default. Before complete defect evidence,
translation must:

- retain the implemented neutral valence electron count derivation in exact
  mapping evidence;
- retain the implemented `delta_n_electrons` conversion in exact mapping
  evidence;
- retain spin mode, initial moments, and spin-channel constraints as separate
  mappings;
- preserve the exact ordered pseudopotential requirement used to interpret that
  electron count;
- return a neutral `CalculatorInputRecord` for INCAR, KPOINTS, POSCAR, and all
  external requirements; and
- reject unsupported charge or spin intent instead of relying on VASP defaults.

Neutral Si:P requires a spin-polarized doublet with
`delta_n_electrons == 0`. Its odd neutral electron count arises from the
substituted P pseudopotential, not from adding a charged-cell electron.

A VASP relaxation input translator with the same charge, spin, cell-mode, and
exact-input behavior is still required before the complete defect workflow can
advertise VASP relaxation support. Rendering does not authorize execution.
