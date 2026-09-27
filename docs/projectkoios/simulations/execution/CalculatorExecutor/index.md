# `CalculatorExecutor`

The public `execute` action first rejects requests without explicit execution
authorization. It then verifies every `required_input_filename`, opens explicit
stdout and stderr files, invokes the declared command without a shell or stdin,
and atomically writes `execution.json`. It returns `CalculatorExecutionRecord`
only for return code zero. The public `record_preflight_failure` action requires
the same explicit authorization before it lets calculator-specific staging
integrations durably record repository-resolution or staging exceptions and
raise the same `CalculatorExecutionError`. For
a missing required input, nonzero exit, launch failure, or timeout, it writes the
failure record first and then raises `CalculatorExecutionError`.
