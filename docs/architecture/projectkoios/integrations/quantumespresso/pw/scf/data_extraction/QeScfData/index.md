# `QeScfData`

Unified immutable SCF facade containing a composed `QePwDataSources` record
with:

- parsed stdout and stderr with exact artifact identities;
- parsed successful execution evidence and its exact artifact identity;
- the normalized calculator-neutral `PwDftScfObservation`;
- optional supplied parsed QEXSD data and interpreted final structure; and
- mechanical cross-source consistency observations.

Convenience properties preserve the former direct extractor access to SCF
energy, cutoff, counts, completion, convergence, diagnostics, and native
artifact identity.
