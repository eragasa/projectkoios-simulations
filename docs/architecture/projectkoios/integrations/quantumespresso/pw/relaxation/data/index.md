# `QeRelaxData`

`QeRelaxData` is the single immutable output-data facade for both Quantum
ESPRESSO `relax` and `vc-relax` calculations. Its `calculation` field retains
the native mode instead of using nominal mode-specific data subclasses.

The facade uses `QePwDataSources` to compose, rather than flatten,
independently sourced observations:

- exact stdout and stderr artifacts and their parsed summaries;
- the complete stdout-observed relaxation trajectory;
- the supplied parsed QEXSD document record and interpreted final structure,
  when available;
- an optional calculator execution record; and
- mechanical cross-source consistency observations.

Convenience properties expose commonly requested values (`stdout`, `stderr`,
`trajectory`, `steps`, `final_structure`, and native completion observations)
without discarding their source records.

`QeRelaxationConsistency` compares only unambiguous mechanical facts such as
terminal status and atom count. It does not decide scientific acceptance,
convergence quality, or numerical equivalence.

`QeQexsdRelaxationData.document` deliberately retains the entire immutable
document record supplied by `QuantumEspressoXsdDocumentParser`. The facade does
not further truncate that record to the interpreted final structure and does
not reimplement XML parsing. Which XML sections the document record models
remains the responsibility of that parser.

`QeRelaxDataExtractor.extract_stream()` and
`QeVcRelaxDataExtractor.extract_stream()` tee binary stdout exactly once to a
new destination while feeding a compact incremental trajectory/summary
projection. Full stdout is not buffered. SHA-256 is computed from the completed
stored artifact after the tee leaves the process-output hot path. The ordinary
offline `extract()` methods remain available.

`QeVcRelaxData` is a compatibility alias of `QeRelaxData`.

## Required neutral observation adapter

Before defect-structure publication, `QeRelaxData` must be adapted into the
planned protected `PwDftRelaxationObservation` and
`PwDftRelaxationResult`. The adapter identifies the source of final positions,
lattice, energy, forces, stress/pressure, ionic convergence, charge, and spin
observations and retains source disagreements.

For fixed-cell relaxation, the exact input lattice remains authoritative and a
printed lattice is consistency evidence. For variable-cell relaxation, the
qualified final observed lattice becomes part of the normalized structure. The
adapter performs no structure-library mutation and makes no scientific
acceptance decision.
