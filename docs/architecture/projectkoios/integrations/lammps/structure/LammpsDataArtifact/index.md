# `LammpsDataArtifact`

**Implemented in:** `projectkoios.integrations.lammps.structure`

Immutable in-memory result of deterministic LAMMPS data rendering.

The artifact validates `atom_style`, unique valid `species_order`, exact
`source` as `PypospackLammpsProvenance`, final-newline `utf8_text`, and the 1 GB
serialized bound. It derives `sha256` from UTF-8 output bytes.

`to_dict(include_text=False)` emits contract
`projectkoios.integrations.lammps-data` version `0.1.0`, source
provenance, digest, byte size, and explicit false execution/scientific claims.
Text is omitted by default and included only when explicitly requested.
