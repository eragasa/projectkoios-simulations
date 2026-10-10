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

For spin-polarized calculations, the stdout parser retains QE's total and
absolute magnetization in native Bohr-magneton-per-cell units. SCF extraction
normalizes total magnetization to the numerically equivalent collinear
spin-channel electron difference; unavailable quantities remain explicit and
are not reconstructed from requested input.

Charged or spin-polarized defect extraction still requires correlation with the
exact `CalculatorInputRecord` and normalization of reported electron count,
spin-channel populations, and background-charge observations when QE supplies
them.

A result is eligible for DFT defect-energy qualification only when its
calculation identity, charge convention, spin intent, total energy, completion,
and SCF convergence are consistent. Parsing those facts does not constitute
scientific acceptance.
