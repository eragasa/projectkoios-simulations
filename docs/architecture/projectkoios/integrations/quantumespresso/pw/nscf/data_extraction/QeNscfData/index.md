# `QeNscfData`

Unified immutable NSCF facade containing a composed `QePwDataSources` record
with:

- parsed stdout and stderr with exact artifact identities;
- the supplied parsed QEXSD document and interpreted final structure;
- `QeNscfSpectralData` with source-ordered k-points, weights, eigenvalues, and
  optional occupations;
- mechanical terminal and declared-shape consistency observations; and
- an optional typed calculator execution record.

Compatibility properties expose the previously flattened spectral and QEXSD
identity fields. Values remain native: extraction does not silently normalize
units, coordinates, weights, energy references, or spin semantics.
