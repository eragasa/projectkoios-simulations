# `CalculatorExecutionRequest`

Immutable request with public `command`, `working_directory`, `stdout_filename`, `stderr_filename`, `record_filename`, `required_input_filenames`, and `timeout_seconds` fields. `command` is passed directly to `subprocess.run` without a shell. The working directory must already exist and must not be a symlink. Output names are distinct basenames within that directory. Every required input basename must resolve to an existing regular nonsymlink file before process launch.
