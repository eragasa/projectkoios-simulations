# `projectkoios.integrations.quantumespresso`

Quantum ESPRESSO-specific specializations of calculator-neutral simulation
records. [`pw`](pw/index.md) owns behavior specific to `pw.x`, including its
single [`inputfile`](pw/inputfile/index.md) component vocabulary.
[`outputs`](outputs/index.md) retains only the implemented captured-stream
contracts shared by current `pw.x` modes. [`pw.execution`](pw/execution/index.md)
resolves exact repository pseudopotentials, stages verified inputs, and executes
`pw.x` with durable failure records.

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
