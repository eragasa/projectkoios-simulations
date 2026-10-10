# `CalculatorExecutor`

The public `action` method first rejects requests without explicit execution
authorization. It then verifies every `required_input_filename`, opens explicit
stdout and stderr files, and invokes the declared command without a shell or
stdin in a new POSIX session. Independent bounded-chunk drain threads retain each
native chunk, then write and flush the same bytes to the corresponding parent
binary stream. The one-process MVP intentionally applies parent-stream
backpressure: supported parent writes must return. Cancellable arbitrary blocked
sinks require a different future delivery policy.

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
remains retained. Timeout terminates the complete isolated process group with a
bounded terminate-then-kill sequence and bounded post-kill verification of the
direct child and complete group. On termination failure, the executor aborts
further source reads before joining stream pumps so a surviving descendant that
holds an inherited pipe cannot suppress the terminal record; an active parent
write still obeys ordinary tee backpressure. Termination failure is recorded as
`failed-to-terminate`. A retained-output failure takes
precedence over coincident timeout while retaining the timeout detail.
