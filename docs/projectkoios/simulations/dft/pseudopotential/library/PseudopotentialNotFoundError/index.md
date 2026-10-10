# `PseudopotentialNotFoundError`

Raised when no deployment entry with the exact required basename exists beneath
the configured `PseudopotentialLibrary` root.

A not-found result does not permit fallback to another family, an element-only
match, or a differently named file. It grants no execution authority.
