# `projectkoios.integrations.quantumespresso.pw.execution`

`QeSimulationExecutor` consumes an exact `CalculatorInputRecord`, verifies its
Quantum ESPRESSO representation and external pseudopotential requirements,
resolves every bound `PseudopotentialFile` through an injected
`PseudopotentialLibrary`, stages the verified artifact bytes, and only then
delegates an explicitly authorized process launch to `CalculatorExecutor`.

An undeclared, missing, symlinked, size-mismatched, or hash-mismatched
pseudopotential produces durable failed-preflight execution evidence and raises
`CalculatorExecutionError` before `pw.x` starts. A prepared input record,
resolved library, or test selection never grants execution authority.
