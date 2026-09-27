# `projectkoios.integrations.quantumespresso.pw.execution`

`QeSimulationExecutor` resolves every exact `QuantumEspressoSimulation.pseudopotential` through `PseudopotentialRepository`, stages verified bytes and rendered `pw.in`, and only then delegates process execution to `CalculatorExecutor`.

An undeclared, missing, symlinked, size-mismatched, or hash-mismatched pseudopotential produces a durable `failed-preflight` `execution.json` and raises `CalculatorExecutionError` before `pw.x` starts.
