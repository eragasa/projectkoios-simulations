# `CalculatorExecutionRequest`

Immutable request with public `command`, `working_directory`, `stdout_filename`,
`stderr_filename`, `record_filename`, `required_input_filenames`,
`timeout_seconds`, and `execution_authorized` fields. Authorization defaults to
`False` and must be set explicitly before execution. `command` is passed
directly to `subprocess.run` without a shell. The working directory must already
exist and must not be a symlink. Output names are distinct basenames within that
directory. Every required input basename must resolve to an existing regular
nonsymlink file before process launch.
