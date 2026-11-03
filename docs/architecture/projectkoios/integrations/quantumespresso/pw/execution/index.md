# `projectkoios.integrations.quantumespresso.pw.execution`

`QeSimulationExecutor` consumes an exact `CalculatorInputRecord`, a
`CalculatorExecutableBinding`, and exact pseudopotential requirements. It
verifies the deployed executable identity, resolves every bound
`PseudopotentialFile` through an injected `PseudopotentialLibrary`, stages a
private reverified executable copy and the verified input bytes, and only then
delegates an explicitly authorized process launch to `CalculatorExecutor`.

An undeclared, missing, symlinked, size-mismatched, or hash-mismatched
executable or pseudopotential produces durable failed-preflight execution
evidence and raises `CalculatorExecutionError` before `pw.x` starts. A prepared
input record, resolved library, executable preparation result, or test
selection never grants execution authority.
