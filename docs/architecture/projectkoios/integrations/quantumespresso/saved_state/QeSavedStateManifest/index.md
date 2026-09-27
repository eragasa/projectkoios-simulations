# `QeSavedStateManifest`

Fields:

- `schema_version`
- `prefix`
- `calculation`
- `producer_program`
- `producer_version`
- `executable_sha256`
- `input_sha256`
- `structure_id`
- `structure_sha256`
- `pseudopotentials`
- `artifacts`

Version one requires exactly one QEXSD artifact, exactly one charge-density
artifact, at least one wavefunction artifact, and one matching saved-state
artifact for every pseudopotential lineage entry under `prefix.save`.
