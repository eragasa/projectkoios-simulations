# `QeRelaxationInputConfiguration`

Immutable shared fields are `species`, `ion_dynamics`,
`charge_density_cutoff_ratio`, `electronic_tolerance_ry`,
`electronic_atol_ry`, `prefix`, `pseudo_dir`, `outdir`, `input_filename`, and
`coordinate_precision`.

`electronic_tolerance_ry` is rendered as QE `conv_thr`.
`electronic_atol_ry` is a finite, nonnegative absolute comparison tolerance in
Ry used only to qualify the neutral-eV-to-native-Ry mapping. It does not alter
the convergence threshold.
