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

## Required defect extension

For charged or spin-polarized defect calculations, extraction must correlate the
retained output with the exact `CalculatorInputRecord` and normalize the
reported electron count, total magnetization, spin-channel populations, and
background-charge observations when QE supplies them. Unavailable quantities
remain explicit; they are not reconstructed from the requested input.

A result is eligible for DFT defect-energy qualification only when its
calculation identity, charge convention, spin intent, total energy, completion,
and SCF convergence are consistent. Parsing those facts does not constitute
scientific acceptance.
