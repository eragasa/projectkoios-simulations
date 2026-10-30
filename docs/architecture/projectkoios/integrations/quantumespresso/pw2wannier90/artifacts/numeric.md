# `pw2wannier90` route-specific artifact numerical contract

## Purpose

This contract separates exact provider artifact closure from consumer-owned
scientific tolerances. Route kind, roles, safe names, byte sizes, SHA-256,
integer dimensions, source indices, spin semantics, and producer identities are
exact. Floating-point physical comparisons require explicit units, metrics, and
prospective tolerances outside the artifact-identity check.

## AMN/MMN localization profile

Let:

```text
N_k  reciprocal-point count
N_b  interface band count
N_p  AMN projection-function count
N_n  MMN neighbor count per source point when uniform
```

The ordinary profile requires exactly one seed-bound EIG, AMN, and MMN artifact.
The implemented native headers provide AMN dimensions `(N_b, N_k, N_p)` and MMN
dimensions `(N_b, N_k, N_n)`. The first two dimensions must agree. EIG must
contain exactly one finite value for every one-based `(band, k-point)` pair in
the complete `N_b * N_k` grid.

The provider also correlates `N_k`, reciprocal-point source order, neighbor
inventory, parent band inventory, seedname, spin semantics, NNKP identity, and
parent NSCF identity. UNK cardinality is not part of this profile.

## Explicit UNK-producing profile

A supported UNK profile declares the exact expected inventory. For a scalar
spin-channel route, each native artifact binds one reciprocal-point index and
the declared selected spin channel. A noncollinear/spinor route uses its
reviewed native component convention rather than pretending to be multiple
scalar channels.

The profile verifies:

- contiguous or otherwise explicitly declared reciprocal-point indices;
- no duplicate logical or physical artifacts;
- exact file byte size and digest;
- FFT-grid dimensions and ordering convention;
- band and spinor/component dimensions;
- agreement with parent QEXSD and converter occurrence; and
- positive bounded total artifact count and byte size.

The exact cardinality formula depends on the declared native spin/component
route and must be reviewed with its decoder. It must not be generalized into a
one-UNK-per-point rule for every possible spin branch without evidence.

## Optional role profiles

SPN, `uHu`, `uIu`, or another native output receives its own role cardinality,
shape, unit, index, and parent-correlation rules. Optional means optional for a
specific declared route, not “accept any file if present.” A closed retained-
evidence profile rejects undeclared selected roles or records them under an
explicit non-promoted observation policy. It does not require every incidental
file in a private native work directory to be absent.

## Identity and path safety

Every declared artifact uses a safe basename or run-root-relative path, positive
byte size, lowercase SHA-256, and exact producer execution-record identity.
Verification rejects symlinks, path traversal, duplicate paths, disallowed hard
links, files outside the declared root, missing files, changed bytes, and
artifact totals above reviewed bounds.

Storage location is not identity. Moving authenticated bytes does not change
their content identity, while replacing bytes at the same path creates a
mismatch.

## Cross-route separation

An AMN/MMN observation cannot be cast to a UNK-producing observation merely by
adding filenames. The route kind participates in identity, and the complete
route-specific constraints must be satisfied. Likewise, the specialized route
does not invalidate an ordinary observation that correctly declared no UNK
consumer.

Downstream localization outputs—WOUT, gauge/disentanglement matrices, and
real-space Hamiltonians—have separate producer occurrences and are not counted
as converter outputs.

## Failure and nonclaims

Missing required roles, duplicate roles, changed bytes, malformed headers,
non-finite EIG values, incomplete index grids, inconsistent dimensions, mixed
parentage, or unsupported optional-role requests fail before a successful
handoff. Failures remain evidence and do not authorize retry.

Exact provider consistency does not establish numerical convergence,
localization quality, or scientific validation. No threshold or check here
grants calculator execution.
