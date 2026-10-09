# `PseudopotentialLibrary`

Immutable deployment resolver rooted at one explicit absolute, existing, nonsymlink directory. `resolve` recursively searches only for the exact basename carried by a complete `PseudopotentialFile` requirement, rejects candidates outside the resolved root or reached through symlinks, and returns a deterministic path only when byte size and SHA-256 both match. Same-named files with other bytes produce `PseudopotentialIntegrityError`; an absent basename produces `PseudopotentialNotFoundError`.

`build_repository` converts a tuple of exact scientific requirements into a `PseudopotentialRepository` whose entries are independently verified again when consumed. The library does not select a family, exchange-correlation approximation, formalism, relativistic treatment, or cutoff, and does not download files or authorize calculator execution.
