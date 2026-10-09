# `PseudopotentialRepositoryEntry`

Frozen, slotted binding with public fields:

- `pseudopotential_file: PseudopotentialFile` — the complete scientific and byte
  identity required by the caller; and
- `path: pathlib.Path` — the explicitly declared local location.

Construction validates types only and raises `TypeError` for invalid values. It
does not require the path to exist and does not read bytes. Availability,
regular-file/nonsymlink status, byte size, and SHA-256 are checked later by
`PseudopotentialRepository.resolve()`.
