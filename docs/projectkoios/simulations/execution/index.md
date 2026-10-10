# `projectkoios.simulations.execution`

The typed action path is `CalculatorExecutionRequest -> CalculatorExecutor ->
CalculatorExecutionRecord`: a frozen, slotted `DataObject` passes through its
`DataObjectActionizer` and produces a frozen, slotted `ResultsObject`. Stdout and
stderr are the intentional byte-stream exception. The execution module defines
no dangling functions and no static or class methods.

`CalculatorExecutionRequest` declares an explicit no-shell process invocation
and carries fail-closed execution authorization. `CalculatorExecutor` rejects an
unauthorized request, retains and emits stdout and stderr for an authorized
request, and atomically writes a `CalculatorExecutionRecord` as JSON before it
returns success or raises a recorded `CalculatorExecutionError`.
`CalculatorOutputEmissionError` separately reports a live-console failure after
native output retention and terminal recording. `ExecutionStatus` distinguishes
successful, failed-preflight, nonzero, start-failure, termination-failure,
retained-output-failure, and timeout outcomes.

The caller owns staging, explicit executable authorization, environment
qualification, and scientific interpretation. The executor does not download
resources, invoke a shell, or treat process success as numerical or scientific
validation.
