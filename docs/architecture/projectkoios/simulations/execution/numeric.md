# Single-simulation execution numerical contract

## Byte preservation

```mermaid
flowchart LR
    native[Ordered calculator stdout bytes]
    chunks[Bounded transport chunks]
    artifact[Retained byte sequence]
    tee[Parent-stream write and flush]
    live[Live operational sink]
    identity[Byte size and SHA-256]
    excluded[Chunk boundaries and flush count]

    native --> chunks
    chunks --> artifact --> identity
    chunks --> tee --> live
    chunks -. operational only .-> excluded
    excluded --x identity
```

The retained stdout artifact is the ordered byte sequence read from the
calculator's stdout pipe. When live emission succeeds, the MVP sink receives the
same chunks in the same stdout order. A write that raises may leave a live prefix
and produces an operational error without changing already retained bytes. A
write that does not return applies ordinary tee backpressure and is outside the
supported parent-sink contract. Chunk boundaries, write-call counts, terminal
rendering, and
flush timing are operational details and do not participate in artifact
identity.

The retained artifact identity is computed from its final byte size and
SHA-256. The executor must not normalize newlines, replace invalid text,
transcode encodings, strip control characters, or append presentation text.
Provider parsers decide later whether and how those bytes represent text.

Stderr is retained as a separate ordered byte sequence. The executor does not
claim a total ordering between stdout and stderr unless a future process-capture
contract records such ordering explicitly.

## Stream progress and buffering

The executor emits stdout promptly after receiving each bounded chunk and
flushes the live sink so an operator can observe progress. This is best-effort
with respect to the calculator: a provider or language runtime may buffer output
before it reaches the pipe. The executor must not claim a physical timestep,
SCF-iteration boundary, or bounded progress latency from receipt timing alone.

The implementation drains stdout and stderr concurrently. Each drain path first
flushes its retained-artifact chunk and then writes and flushes the same chunk to
the corresponding parent binary stream. This preserves byte identity without
accumulating complete output in memory. It also intentionally propagates parent
stream backpressure. Cancellable delivery to arbitrary blocked sinks is deferred
to a future runtime-control design because it is incompatible with the selected
one-process, byte-exact MVP boundary.

## Timeout and termination

`timeout_seconds`, when present, is a positive finite duration for one process
attempt. Timeout measurement uses a monotonic elapsed-time source. On timeout,
the POSIX implementation terminates the isolated process group using a bounded
terminate-then-kill escalation and bounded post-kill verification of both the
direct child and complete process group, drains available pipe bytes, closes
retained artifacts, writes a terminal execution record, and raises the recorded
error. A signal or post-kill failure records
`failed-to-terminate`. On termination failure, it stops further source reads
and closes its local pipe endpoints before joining drain threads; this prevents
a quiet surviving descendant from withholding the terminal record by retaining
an inherited pipe. A parent-stream write already in progress remains subject to
ordinary tee backpressure. The executor fails preflight on platforms where this
process-group guarantee is not implemented.

Bytes received before terminal cleanup remain in their native artifacts. The
execution record does not fabricate a return code when none was observed.
Nonzero exits retain the observed integer return code; successful records
require return code zero. If timeout coincides with a retained-stream failure,
`failed-output` takes precedence because the authoritative evidence is
incomplete; its error message also retains the timeout detail.

Exact termination escalation and grace intervals require an implementation
contract before they become public configuration. They must not be silently
reinterpreted as scientific convergence limits.

## Concurrency cardinality

For each call:

```text
number of CalculatorExecutionRequest values = 1
maximum calculator subprocesses started     = 1
maximum terminal CalculatorExecutionRecord  = 1
```

A preflight failure starts zero subprocesses and still writes one failure
record after explicit authority has been established. A deployment-wide
concurrency limit is not represented by these cardinalities; it is a runtime
admission setting.

## Identity exclusions

The following do not alter scientific specification or calculator-input
identity:

- terminal width or color support;
- whether an operator is attached;
- live-sink chunk size;
- console flush count;
- progress-message formatting; and
- a future controller's transport destination.

They may be retained as operational telemetry under a separately versioned
runtime contract, but they are excluded from normalized scientific
observations.

## Numerical verification

Deterministic helper-process tests must compare emitted and retained byte
sequences across multiple chunk sizes, embedded non-UTF-8 bytes, missing final
newlines, large stdout/stderr volumes, nonzero exit, and timeout. These tests
verify process and byte-handling behavior only; they do not execute or validate
a scientific calculator.
