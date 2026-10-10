# `relaxation.projection`

`project_relaxation_input` assembles common `pw.x` card types after the
`relax` or `vc_relax` package validates mode-specific policy.

`QeIonicRelaxationOptions` explicitly binds the ionic optimizer, maximum ionic
steps, and energy and force tolerances used by both modes.
`QeLatticeVectorRelaxationOptions` separately binds the cell optimizer, allowed
lattice degrees of freedom, target pressure, and pressure tolerance required by
`vc-relax`.

`QeRelaxationInputProjection` is the explicit provider-owned aggregate. It
retains those option records, the common QE cards, and the neutral rendered
input. Fixed-cell `relax` forbids lattice-vector options and a `&CELL` card;
`vc-relax` requires both. No nominal mode-specific card subclasses are
introduced when a common card already represents the native section.

## Defect extension status

Relaxation translation now maps integral `delta_n_electrons` through QE's
positive-charge convention, renders collinear mode and a constrained
spin-channel difference for both fixed-cell and variable-cell calculations,
checks exact bound pseudopotential filenames, and rejects unsupported
site-resolved initial moments. It still must represent supported initialization,
occupation policy, and every implemented conversion in a complete
`CalculatorInputRecord`.

Variable-cell translation must also map the explicitly selected cell-relaxation
mode into QE's allowed cell degrees of freedom. No QE default may decide whether
volume, shape, or individual lattice components change. Symmetry and starting-
geometry policies are likewise explicit inputs.

A neutral Si:P ion-only or ion-and-cell relaxation that lacks the declared
spin-polarized doublet intent is not an eligible rendering for the defect study.
Rendering does not authorize `pw.x` execution.
