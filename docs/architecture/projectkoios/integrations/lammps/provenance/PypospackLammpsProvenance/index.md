# `PypospackLammpsProvenance`

**Source:** `src/python/projectkoios/integrations/lammps/provenance.py`

Immutable exact-source declaration for the PyPosPack LAMMPS integration.

Fields are `component`, `repository_url`, `release_tag`, `revision`, `tree`,
`source_path`, `source_sha256`, `source_byte_size`, `license_path`,
`license_sha256`, and `source_limitations`. Construction rejects any value that differs from the
maintained binding.

The release tag is `v0.1.0`; the exact commit and tree remain the immutable
source identity. `to_dict()` returns deterministic JSON-ready provenance
without a machine-local checkout path. The object grants no source-fetch or execution authority.
