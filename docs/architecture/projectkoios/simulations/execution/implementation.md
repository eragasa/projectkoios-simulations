# Single-simulation calculator execution implementation

## Request and process invariants

The typed action path is:

```text
CalculatorExecutionRequest -> CalculatorExecutor -> CalculatorExecutionRecord
```

The request is a frozen, slotted `DataObject`; the record is a frozen, slotted
`ResultsObject`. `CalculatorExecutor` implements their `DataObjectActionizer`
and owns its private runtime operations as instance methods;
the module defines no dangling functions and uses no static or class methods.
Stdout and stderr remain byte streams rather than data-object results.

`CalculatorExecutor.action()` remains a synchronous one-request operation. It
must:

1. reject absent execution authorization before starting or staging a process;
2. validate the request and required input files;
3. reject symbolic-link output destinations;
4. invoke exactly the declared command with `shell=False` and no interactive
   stdin;
5. start no more than one subprocess;
6. wait for that subprocess to terminate or reach the declared timeout;
7. close and flush retained output artifacts; and
8. atomically write one terminal `execution.json` record before returning or
   raising `CalculatorExecutionError`.

No plural request, batch method, campaign loop, convergence loop, retry loop, or
background process registry belongs in this class.

## MVP output tee

The implemented stdout path is a byte-preserving tee:

```text
calculator stdout bytes
        |
        +--> declared stdout artifact
        `--> parent process stdout
```

The implementation does not decode and re-encode calculator output before
writing the retained artifact. It uses bounded raw-byte chunks and flushes each
artifact chunk before writing the same chunk to the corresponding parent binary
stream. Successful live emission therefore preserves byte order and content.

The one-process MVP intentionally applies ordinary Unix tee backpressure: a
supported parent stream must expose a binary buffer and its writes must return.
A slow parent may delay calculator progress, and a parent sink that never returns
can block the invocation. Providing cancellable delivery to an arbitrary blocked
sink would require relaxing the one-process contract or allowing prefix-only
best-effort output; neither belongs to this MVP. If a live write raises, that
stream disables further emission while native-artifact retention continues. The
executor writes the accurate process-terminal record and then raises
`CalculatorOutputEmissionError`; console availability therefore does not
reclassify the calculator process attempt. A retained-stream failure instead
produces `failed-output` because authoritative native evidence is incomplete.
When timeout and retained-stream failure coincide, `failed-output` takes
precedence and the error message retains the timeout detail, including failures
from retained-file or stream cleanup outside the ordinary pump loop.

Stderr uses its own retained file and drain thread so a verbose calculator cannot
block on a full pipe. Its raw chunks are mirrored to parent stderr without
combining stdout and stderr in retained evidence.

Output already received remains on disk after timeout or process failure. The
execution record is written only after stream draining completes and process
termination reaches its bounded terminal state. Stream draining remains subject
to the selected parent-sink backpressure contract above.

The MVP execution backend requires POSIX process-group isolation. Each attempt
starts a new session. Timeout first signals the complete process group to
terminate, waits a bounded grace interval, and then kills any surviving group
members before exposing the terminal record. The post-kill wait verifies both
direct-child reaping and complete process-group disappearance within a bound.
A group-signal or post-kill failure aborts further source-pipe reads before
joining the pump threads, so a quiet surviving descendant cannot suppress the
`failed-to-terminate` record merely by retaining an inherited pipe. An
already-running parent-stream write still obeys policy-A backpressure and is not
interrupted. Termination failure is recorded as `failed-to-terminate`, never as
`failed-to-start`; a best-effort bounded direct-child kill limits leakage.
Unsupported platforms fail preflight rather than claim descendant cleanup they
cannot provide.

## Output-emission seam

The MVP keeps the emission seam private. It has one nominal responsibility:
accept an ordered byte chunk for one stream and write it to the supported parent
binary stream after artifact retention. Provider integrations do not call the
seam directly.

A later control implementation may replace console emission with a runtime-owned
sink that produces progress messages or accepts cancellation. That replacement
must preserve:

- byte-exact native artifacts;
- source ordering within each stream;
- the selected live-output backpressure or truncation policy;
- one process per execution request;
- the terminal execution-record contract;
- explicit authorization; and
- separation between operational control and scientific acceptance.

The control sink is not serialized into `CalculatorExecutionRequest` or
`CalculatorExecutionRecord` because it is deployment state, not calculation
identity.

## Scheduling and workflow ownership

An external Workflow runner selects one occurrence, calls the executor, consumes
its terminal record, and only then selects another occurrence when configured
for concurrency one. Queueing, leasing, cancellation reconciliation, retries,
and durable delivery stay outside `projectkoios.simulations.execution`.

A retry creates another attempt and another execution record for the same
transition occurrence. A new convergence coordinate, defect start, or supercell
size creates a new scientific request and occurrence.

## Verification requirements

Focused tests must establish:

- unauthorized requests start no process and emit no calculator output;
- one request launches exactly one subprocess;
- when live emission succeeds, emitted stdout bytes equal the retained stdout
  artifact bytes;
- stderr cannot deadlock stdout draining;
- supported live sinks receive the retained stdout bytes in order;
- raised live-write errors do not stop authoritative artifact retention;
- stream completion waits for a parent write to return under ordinary tee
  backpressure;
- a stream-pump bootstrap failure after process launch cleans up the process and
  any started pump before writing a `failed-output` terminal record;
- partial output survives nonzero exit and timeout;
- timeout terminates calculator descendants in the isolated process group;
- termination failure aborts source reads held open by an unresponsive
  descendant and still writes `failed-to-terminate`;
- retained-output failure takes precedence over coincident timeout;
- success and every failure path write exactly one terminal record;
- no shell or interactive stdin is introduced; and
- the executor exposes no batch, queue, retry, or campaign behavior.

Tests use deterministic helper processes and never invoke a scientific
calculator. Repository-wide tests, Ruff, formatting, strict mypy, wheel build,
and `git diff --check` remain required.
