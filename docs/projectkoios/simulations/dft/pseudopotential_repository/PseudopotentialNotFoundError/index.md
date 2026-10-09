# `PseudopotentialNotFoundError`

Raised when the requested exact deployment location is unavailable.

- `PseudopotentialLibrary.resolve()` raises it when no entry with the required
  basename exists beneath the configured root.
- `PseudopotentialRepository.resolve()` raises it when the complete required
  `PseudopotentialFile` is undeclared or its declared path is not a currently
  available regular nonsymlink file.

A not-found result does not permit fallback to another family, element match, or
same-named file.
