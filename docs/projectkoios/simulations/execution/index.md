# `projectkoios.simulations.execution`

`CalculatorExecutionRequest` declares an explicit no-shell process invocation. `CalculatorExecutor` captures stdout and stderr and atomically writes a `CalculatorExecutionRecord` as JSON before it returns success or raises `CalculatorExecutionError`. `ExecutionStatus` distinguishes successful, failed-preflight, nonzero, start-failure, and timeout outcomes.

The caller owns staging, executable authorization, environment qualification, and scientific interpretation. The executor does not download resources, invoke a shell, or treat process success as numerical or scientific validation.
