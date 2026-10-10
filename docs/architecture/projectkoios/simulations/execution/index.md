# Single-simulation calculator execution

## Purpose

`projectkoios.simulations.execution` owns the calculator-neutral process boundary
for one explicitly authorized calculator attempt. One call consumes one
`CalculatorExecutionRequest`, starts at most one subprocess in one working
directory, retains its terminal record, and returns only after that attempt has
terminated.

The executor is not a campaign runner. It does not enumerate simulation
specifications, schedule multiple calculations, retry an occurrence, decide
convergence, select a defect basin, or grant execution authority. Those
responsibilities belong to an external Workflow runtime and scientific workflow
composition.

## Current and MVP behavior

The current executor is already synchronous and single-request: it launches one
no-shell process and writes stdout, stderr, and `execution.json` into the
request's working directory. It currently directs calculator stdout only to the
retained file.

The required MVP adds live output observability:

- calculator stdout is emitted to the parent process's stdout while the same
  bytes are retained in the declared stdout artifact;
- partial stdout remains retained after nonzero exit, launch failure after
  output begins, cancellation, or timeout;
- stderr remains a separate retained artifact and should be mirrored to the
  parent process's stderr when the execution implementation supports it; and
- stream emission never changes scientific identity, evidence identity, terminal
  status, or authorization.

The retained artifacts are authoritative evidence. Console output is
operational observability only.

## Concurrency boundary

"One simulation at a time" has two layers:

1. one executor invocation starts at most one calculator process; and
2. the external Workflow runner admits no second calculator occurrence until
   the first invocation returns.

The protected executor can enforce the first invariant. It must not implement a
machine-global lock, queue, lease, or scheduler in an attempt to enforce the
second. A deployment that requires global concurrency one configures that limit
in its Workflow runtime.

## Future control boundary

MVP stdout emission must pass through one narrow internal output-emission seam,
not through provider-specific `print()` calls. The MVP implementation writes raw
chunks to `sys.stdout.buffer`. A future controller may replace that sink with
progress events, remote streaming, cancellation input, or another control
channel without changing calculator input records or retained native artifacts.

The future seam is an execution-runtime concern. It is not a field of a
scientific specification and cannot infer completion, convergence, acceptance,
or authority from displayed output.

See [`implementation.md`](implementation.md) for process and evidence rules,
[`schematics.md`](schematics.md) for the single-attempt and campaign boundaries,
[`scientific.md`](scientific.md) for the limit of execution evidence, and
[`numeric.md`](numeric.md) for byte, stream, timeout, and cardinality contracts.
