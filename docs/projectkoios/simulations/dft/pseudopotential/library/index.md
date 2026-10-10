# `projectkoios.simulations.dft.pseudopotential.library`

[`PseudopotentialLibrary`](PseudopotentialLibrary/index.md) locates exact,
caller-selected `PseudopotentialFile` bytes beneath one explicit machine-local
root. Resolution matches basename, byte size, and SHA-256 and rejects symlinks
and paths escaping the configured root.

The library does not maintain a second repository or resolved-entry hierarchy.
Consumers retain the exact requirement together with the verified returned path
when that correlation is needed.

## Error taxonomy

- [`PseudopotentialNotFoundError`](PseudopotentialNotFoundError/index.md) reports
  an absent required basename.
- [`PseudopotentialIntegrityError`](PseudopotentialIntegrityError/index.md)
  reports candidates that exist but do not match the required bytes.
- `TypeError` reports values of the wrong contract type.
- `ValueError` reports an invalid library root.

Filesystem exceptions caused by concurrent removal, permission changes, or I/O
failure are not converted into scientific or integrity decisions.

See [`docs/local-execution.md`](../../../../../local-execution.md) for the
non-authorizing machine-deployment boundary.
