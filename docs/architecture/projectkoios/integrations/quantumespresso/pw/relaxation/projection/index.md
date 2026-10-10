# QE relaxation calculator-input translation

`project_relaxation_input` assembles shared `pw.x` cards after the fixed-cell
`relax` or variable-cell `vc-relax` adapter validates mode-specific policy. The
existing Python API uses “projection”; architecturally this is calculator-input
translation from a neutral relaxation specification and an exact resolved
starting structure.

`QeIonicRelaxationOptions` explicitly binds the ionic optimizer, maximum ionic
steps, and native energy and force tolerances used by both modes.
`QeLatticeVectorRelaxationOptions` separately binds the cell optimizer, allowed
lattice degrees of freedom, target pressure, and pressure tolerance required by
`vc-relax`.

The neutral electronic convergence threshold is stored in eV. The QE
configuration separately carries `electronic_tolerance_ry`, which is rendered
as `conv_thr`, and `electronic_atol_ry`, which only qualifies the eV-to-Ry
comparison.

## Documents

- [Implementation](implementation.md)
- [Schematics](schematics.md)
- [Numeric contract](numeric.md)
- [Scientific semantics](scientific.md)

## Provider aggregate

`QeRelaxationInputProjection` retains native option records, common QE cards,
and rendered input. Fixed-cell `relax` forbids lattice-vector options and a
`&CELL` card; `vc-relax` requires both. No nominal mode-specific card subclasses
are introduced when a common card already represents the native section.

Relaxation translation maps integral `delta_n_electrons` through QE's
positive-charge convention, renders supported collinear spin and constrained
spin-channel difference, verifies exact bound UPF filenames, maps the declared
cell-relaxation mode to explicit QE degrees of freedom, and fails closed for
unsupported occupation, symmetry, spin, initial-moment, or cell intent.

The translator returns `QeRelaxationInputProjection`, not the required exact
`CalculatorInputRecord`. Completing that atomic result-contract migration
requires exact rendered bytes, external pseudopotential requirements, and all
neutral-to-native mapping observations.

Rendering does not authorize `pw.x` execution and does not establish
convergence or scientific acceptance.
