# `PseudopotentialIntegrityError`

Raised when a deployment location exists for the requested name or declaration
but its bytes do not satisfy the required identity.

- `PseudopotentialLibrary.resolve()` raises it when one or more entries have the
  required basename but none is an acceptable contained regular nonsymlink file
  with the required size and SHA-256.
- `PseudopotentialRepository.resolve()` raises it when a declared regular file's
  observed size or SHA-256 differs from the required identity.

The error reports mechanical byte-identity failure. It is not a scientific
acceptance result and does not authorize substitution.
