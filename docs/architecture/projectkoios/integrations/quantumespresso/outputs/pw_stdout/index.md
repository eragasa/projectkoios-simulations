# `projectkoios.integrations.quantumespresso.outputs.pw_stdout`

Captured `pw.x` stdout composition:

- `QePwStdoutFile`
- `QePwStdoutFileParser`
- `QePwStdoutFileResult`
- `QeStressTensor`

The parser retains native completion and SCF observations plus the final
represented force, pressure, and stress tensor. For BFGS relaxation it also
captures optimizer convergence counts and snapshots the force, pressure, and
stress present when QE reports convergence, separately from any subsequent
final-cell SCF observations. It also distinguishes the fixed-cell energy change
from the variable-cell enthalpy change and retains the native BFGS criteria and reports a
left-handed-axis warning as an observation rather than manufacturing an error.
Values retain QE native units.

These observations do not constitute workflow acceptance. In particular,
`JOB DONE.`, SCF convergence, BFGS convergence, force tolerance, and pressure or
stress tolerance remain separately assessed conditions.
