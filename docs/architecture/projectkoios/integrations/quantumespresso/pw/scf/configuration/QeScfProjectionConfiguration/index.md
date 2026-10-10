# QeScfProjectionConfiguration

Fields: `species`, `charge_density_cutoff_ratio`,
`electronic_tolerance_ry`, `electronic_atol_ry`,
`magnetic_moment_atol_mu_b`, `prefix`, `pseudo_dir`, `outdir`,
`input_filename`, and `coordinate_precision`.

`electronic_tolerance_ry` is the QE-native threshold rendered as `conv_thr`.
`electronic_atol_ry` is a finite, nonnegative absolute tolerance in Ry used only
to compare that native value with the neutral eV threshold after conversion. It
is neither rendered input nor scientific acceptance policy.

`magnetic_moment_atol_mu_b` is the finite, nonnegative absolute tolerance used
only to decide whether site moments for one element can be represented by QE's
single species-level `starting_magnetization(i)` value. It is not a magnetic
acceptance threshold and is not rendered.
