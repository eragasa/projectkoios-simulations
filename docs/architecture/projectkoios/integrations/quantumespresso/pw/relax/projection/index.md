# `relax.projection`

`QeRelaxInputProjector` validates fixed-cell ionic-relaxation policy and returns
an exact `CalculatorInputRecord` assembled from common QE cards. It rejects
variable-cell requests, never creates lattice-vector controls or a `&CELL`
card, and explicitly requests stress output so residual fixed-cell stress can
be retained.
