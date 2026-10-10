# `PseudopotentialIntegrityError`

Raised when one or more deployment files exist for the requested basename but
none satisfies the required exact byte identity.

`PseudopotentialLibrary.resolve()` requires a contained regular nonsymlink file
with the declared byte size and SHA-256. A same-named file that fails those
checks produces this error rather than being accepted or silently substituted.

The error reports mechanical byte-identity failure. It is not a scientific
acceptance result and does not authorize substitution or calculator execution.
