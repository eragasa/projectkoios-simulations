# `projectkoios.simulations.dft.pseudopotential_repository`

This module separates two deployment concerns while retaining caller-owned
scientific selection:

- [`PseudopotentialLibrary`](PseudopotentialLibrary/index.md) discovers the
  deterministic location of caller-required exact bytes beneath one configured
  root.
- [`PseudopotentialRepository`](PseudopotentialRepository/index.md) resolves only
  explicitly declared [`PseudopotentialRepositoryEntry`](PseudopotentialRepositoryEntry/index.md)
  records and re-verifies bytes when consumed.

Both consume complete `PseudopotentialFile` requirements. Neither chooses by
element or family, silently substitutes another artifact, downloads a file,
selects a calculator, or authorizes execution.

## Error taxonomy

- [`PseudopotentialNotFoundError`](PseudopotentialNotFoundError/index.md) reports
  an absent library basename, an undeclared repository requirement, or an
  unavailable declared file.
- [`PseudopotentialIntegrityError`](PseudopotentialIntegrityError/index.md)
  reports same-named library candidates with nonmatching bytes or a declared
  repository artifact whose current size or SHA-256 changed.
- `TypeError` reports values of the wrong public contract type.
- `ValueError` reports an invalid library root or conflicting/non-unique
  repository declarations.

Filesystem exceptions caused by concurrent removal, permission changes, or I/O
failure are not converted into scientific or integrity decisions.

## Deployment flow

```text
caller-selected PseudopotentialFile
                 |
                 v
PseudopotentialLibrary(root).resolve(required)
   exact basename + size + SHA-256
                 |
                 v
PseudopotentialRepositoryEntry(required, path)
                 |
                 v
PseudopotentialRepository.resolve(required)
   re-check regular file + size + SHA-256
```

See [`docs/local-execution.md`](../../../../local-execution.md) for the status
and non-authorizing role of the repository-local deployment template.
