# VaspPwDftScfActionHandler

`integration`, `tasks`, and `executor` are composed dependencies. `register`,
`submit`, and `analyze` implement the common action-handler contract. Execution
is fail-closed unless the task's `CalculatorExecutionRequest` explicitly sets
`execution_authorized=True`. An authorized execution is pre-staged, bounded,
shell-free, and recorded by `CalculatorExecutor`.
