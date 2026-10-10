# `CalculatorExecutor`

The public `execute` action first rejects requests without explicit execution
authorization. It then verifies every `required_input_filename`, opens explicit
stdout and stderr files, and invokes the declared command without a shell or
stdin. Independent bounded-chunk drain threads retain both native streams while
mirroring their exact bytes to the corresponding parent binary streams.

After the single process terminates, the executor atomically writes
`execution.json`. It returns `CalculatorExecutionRecord` only for return code
zero with successful output handling. A live-console failure leaves that
accurate process-terminal record intact and raises
`CalculatorOutputEmissionError`; a retained-stream failure is recorded as
`failed-output`. The public `record_preflight_failure` action requires the same
explicit authorization before it lets
calculator-specific staging integrations durably record repository-resolution
or staging exceptions and raise the same `CalculatorExecutionError`. For a
missing required input, nonzero exit, launch failure, retained-output failure,
or timeout, the executor writes the failure record first and then raises
`CalculatorExecutionError`. Output received before nonzero exit or timeout
remains retained.
