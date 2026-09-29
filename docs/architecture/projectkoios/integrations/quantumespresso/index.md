# `projectkoios.integrations.quantumespresso`

Quantum ESPRESSO-specific specializations of calculator-neutral simulation
records. [`pw`](pw/index.md) owns behavior specific to `pw.x`, including its
single [`inputfile`](pw/inputfile/index.md) component vocabulary.
[`outputs`](outputs/index.md) retains only the implemented captured-stream
contracts shared by current `pw.x` modes. [`pw.execution`](pw/execution/index.md)
resolves exact repository pseudopotentials, stages verified inputs, and executes
`pw.x` with durable failure records. [`pw.nscf`](pw/nscf/index.md) extracts a
closed TOML declaration into inherited QE input cards, verifies and stages a
parent SCF state, executes only with separate authorization, and emits a typed
saved-state handoff for `pw2wannier90.x`.
[`pw.bands`](pw/bands/index.md) projects branched reciprocal paths and extracts
full-precision QEXSD spectra into calculator-neutral diagram records without
using `bands.x` or plotting files.
[`epw`](epw/index.md) renders explicit
`&inputepw` assignments, stages identity-bound parent artifacts, invokes
`epw.x` only with explicit authorization, and inspects declared native evidence
without applying scientific acceptance policy.

The package binds represented data to Quantum ESPRESSO formats without selecting
scientific settings, accessing undeclared external files, or implicitly
executing calculator processes.

## Extraction boundary

The integration depends on calculator-neutral simulation ports and records,
plus PhysKit records. It does not import application packages or workflow
implementations. Parsed QEXSD documents enter through structural protocols; the
integration does not own or duplicate semantic XML parsing. These dependency
directions allow the complete provider package to move without moving workflow
orchestration with it.
