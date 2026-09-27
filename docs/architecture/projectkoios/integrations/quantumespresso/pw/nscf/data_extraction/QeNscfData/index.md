# `QeNscfData`

Fields:

- `streams`
- `source_path`
- `source_sha256`
- `source_byte_count`
- `qexsd_version`
- `producing_application`
- `producing_application_version`
- `declared_unit_system_label`
- source-ordered `k_points`
- `k_point_weights`
- `sampled_k_point_count`
- `k_point_source_label`
- `eigenvalues`
- optional `occupations`
- `eigenvalue_source_label`
- `band_count`
- `exit_status`

Values and source labels remain native; extraction does not silently normalize
units, coordinates, weights, energy references, or spin semantics.
