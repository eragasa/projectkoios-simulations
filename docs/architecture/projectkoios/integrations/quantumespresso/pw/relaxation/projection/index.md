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
projection. Fixed-cell `relax` forbids lattice-vector options and a `&CELL`
card; `vc-relax` requires both. No nominal mode-specific card subclasses are
introduced when a common card already represents the native section.
