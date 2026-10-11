# `QeScfNormalizer`

`QeScfNormalizer.action(...)` is the pure provider-to-neutral normalization
boundary for parsed QE SCF output.

Its immutable request contains `QePwDataSources` with:

- exact parsed stdout and stderr artifact identities;
- successful, path-free `QePwExecutionData`;
- the exact retained execution-record artifact identity; and
- optional interpreted QEXSD data.

The result retains the exact request and one `QeScfData`. Normalization converts
Ry values to eV, maps collinear total magnetization to its neutral electron-spin
difference meaning, creates diagnostics bound to the exact stderr artifact, and
records mechanical stdout/QEXSD consistency. Missing required SCF observations
fail closed.

The normalizer does not read files, start processes, alter source bytes, repair
execution, choose thresholds, establish provider candidacy, grant authority, or
decide scientific acceptance. `QeScfDataExtractor` delegates to this same
actionizer after retained-artifact loading and native parsing.
