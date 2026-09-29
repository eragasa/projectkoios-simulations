# `pw.scf.data_extraction`

SCF-owned retained-data extraction:

- `QeScfData`
- `QeScfExecutionData`
- `QeScfConsistency`
- `QeScfArtifactError`
- `QeScfDataExtractor`

`QeScfData` composes captured native streams, exact execution evidence, the
calculator-neutral `PwDftScfObservation`, optional parsed QEXSD data, and
mechanical consistency observations. `QePwDftScfIntegration.analyze(...)`
continues to return its required calculator-neutral observation by selecting
`QeScfData.observation`.
