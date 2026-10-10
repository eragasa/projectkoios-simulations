# Single-simulation calculator execution implementation

## Request and process invariants

`CalculatorExecutor.execute()` remains a synchronous one-request operation. It
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
writing the retained artifact. It uses bounded raw-byte chunks, flushes each
artifact chunk, and flushes the live sink so an operator can observe progress.
If a parent console stream cannot accept bytes, draining and native-artifact
retention continue. The executor writes the accurate process-terminal record and
then raises `CalculatorOutputEmissionError`; console availability therefore does
not reclassify the calculator process attempt. A retained-stream failure instead
produces `failed-output` because authoritative native evidence is incomplete.

Stderr uses its own retained file and drain thread so a verbose calculator cannot
block on a full pipe. Its raw chunks are mirrored to parent stderr without
combining stdout and stderr in retained evidence.

Output already received remains on disk after timeout or process failure. The
execution record is written only after stream-draining and process termination
have reached a bounded terminal state.

## Output-emission seam

The MVP keeps the emission seam private. Each emitter has one nominal
responsibility: accept an ordered byte chunk for one stream and emit it outside
the retained-artifact writer. Provider integrations do not call the seam
directly.

A later control implementation may replace console emission with a runtime-owned
sink that produces progress messages or accepts cancellation. That replacement
must preserve:

- byte-exact native artifacts;
- source ordering within each stream;
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
- emitted stdout bytes equal the retained stdout artifact bytes;
- stderr cannot deadlock stdout draining;
- partial output survives nonzero exit and timeout;
- success and every failure path write exactly one terminal record;
- no shell or interactive stdin is introduced; and
- the executor exposes no batch, queue, retry, or campaign behavior.

Tests use deterministic helper processes and never invoke a scientific
calculator. Repository-wide tests, Ruff, formatting, strict mypy, wheel build,
and `git diff --check` remain required.
