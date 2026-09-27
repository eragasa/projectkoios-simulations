# `QeNscfProjectionConfiguration`

Explicit native configuration fields:

- `species`
- source-ordered `kpoints`
- reviewed `band_count`
- `wavefunction_cutoff_ry`
- `charge_density_cutoff_ry`
- `electronic_tolerance_ry`
- `occupations`
- `prefix`
- `pseudo_dir`
- `outdir`
- `input_filename`
- `parent_saved_state_manifest_sha256`
- `disable_symmetry`
- `disable_time_reversal`
- `coordinate_precision`
- `kpoint_precision`

K-point weights must sum to one. The maintained Wannier-oriented projection
requires symmetry and inversion reduction to be explicitly disabled.
