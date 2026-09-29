# `relax.projection`

`QeRelaxInputProjector` produces `QeIonicRelaxationOptions` and common QE
cards, retains them in `QeRelaxationInputProjection`, and rejects
variable-cell requests. It never creates lattice-vector options or a `&CELL`
card.
