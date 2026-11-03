# `QeSimulationExecutor`

The public `execute` action accepts a QE `CalculatorInputRecord`, exact bound
`PseudopotentialFile` values, an injected `PseudopotentialLibrary`, a
`CalculatorExecutableBinding`, working directory, optional timeout, and
default-false `execution_authorized`. It rejects an unauthorized request before
observing deployment files or staging attempt artifacts.

For an authorized request, the executor uses `CalculatorExecutablePreparer` to
verify the deployed executable's nonsymlink regular-file type, runnable mode,
byte count, and SHA-256. It then checks that declared external requirements
correspond exactly to the bound pseudopotentials and resolves their deployment
bytes.

The executor stages a private `.projectkoios-pw.x` copy using no-replace
publication, applies owner read-and-execute permissions, and re-verifies the
staged copy against the same executable identity before process entry. It also
stages every prepared input artifact and pseudopotential, then delegates the
single process attempt to `CalculatorExecutor`. Preparation, resolution, or
staging failures are retained as failed-preflight execution records.

The private copy closes mutation between source observation and staging. The
current mutable working-directory path is not yet a descriptor-bound process
entry, so a separately reviewed execution-preparation tranche remains required
to close that final time-of-check/time-of-use boundary. This operational
qualification grants no scientific validity.
