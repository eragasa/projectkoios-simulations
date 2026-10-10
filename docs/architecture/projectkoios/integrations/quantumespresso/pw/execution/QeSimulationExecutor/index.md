# `QeSimulationExecutor`

The public `execute` action accepts a QE `CalculatorInputRecord`, the exact bound
`PseudopotentialFile` values, an injected `PseudopotentialLibrary`, executable,
working directory, optional timeout, and default-false
`execution_authorized`. It rejects an unauthorized request before staging.

For an authorized request, the executor checks that the record's declared
external requirements correspond exactly to the bound pseudopotentials,
resolves and cryptographically verifies their deployment bytes, stages every
prepared input artifact and pseudopotential, and invokes `CalculatorExecutor`.
Resolution or staging failures are recorded before an exception is raised.
