# `QeRelaxInputProjector`

The immutable `configuration` supplies QE-native policy. `project` validates a
fixed-cell request and exact `StructureResolution`, qualifies the neutral eV
electronic threshold against `electronic_tolerance_ry` within
`electronic_atol_ry`, and returns deterministic QE input. Only
`electronic_tolerance_ry` is rendered as `conv_thr`.
