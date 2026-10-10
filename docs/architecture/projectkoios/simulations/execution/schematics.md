# Single-simulation calculator execution schematics

## One attempt

```mermaid
flowchart TD
    authority[Explicit execution authorization]
    request[One CalculatorExecutionRequest]
    executor[CalculatorExecutor.execute]
    process[One calculator subprocess]
    stdoutTee[Byte-preserving stdout tee]
    stderrTee[Independent stderr drain and tee]
    live[Parent stdout and stderr<br/>operational observability]
    stdout[Retained stdout artifact]
    stderr[Retained stderr artifact]
    record[One terminal execution.json]
    terminal{Process outcome}
    success[Return CalculatorExecutionRecord]
    failure[Raise recorded CalculatorExecutionError]

    authority --> executor
    request --> executor
    executor --> process
    process --> stdoutTee
    process --> stderrTee
    stdoutTee --> live
    stdoutTee --> stdout
    stderrTee --> live
    stderrTee --> stderr
    stdout --> record
    stderr --> record
    process --> terminal
    terminal --> record
    record -->|zero return code| success
    record -->|failure or timeout| failure
```

The live stream and retained artifact observe the same calculator bytes, but
only the retained artifact participates in evidence identity.

## Workflow sequencing at concurrency one

```mermaid
sequenceDiagram
    participant W as External Workflow runner
    participant E as Single-simulation executor
    participant P as Calculator process
    participant A as Retained artifacts

    W->>E: execute occurrence A
    E->>P: start one process
    loop native output chunks
        P-->>E: stdout or stderr bytes
        E-->>W: emit live operational output
        E->>A: append exact native bytes
    end
    P-->>E: terminal status
    E->>A: write execution.json
    E-->>W: terminal record for A
    Note over W,E: Only now may concurrency-one admission select B
    W->>E: execute occurrence B
    E->>P: start one process
    P-->>E: terminal status
    E-->>W: terminal record for B
```

The executor contains none of the sequencing between occurrences. It knows only
the request currently passed to it.

## Output and future control

```mermaid
flowchart LR
    process[Calculator process]
    writer[Byte-preserving retained-artifact writer]
    evidence[Native evidence artifact]
    seam[Output-emission seam]
    console[MVP<br/>parent stdout and stderr]
    control[Future runtime control<br/>progress, remote stream, cancellation]

    process --> writer --> evidence
    writer --> seam
    seam --> console
    seam -. future replacement .-> control
    control --x evidence
```

Replacing the operational sink must not replace, filter, reinterpret, or grant
authority to the evidence path.

## Forbidden ownership

```mermaid
flowchart LR
    executor[CalculatorExecutor]
    batch[Campaign enumeration or batching]
    parallel[Parallel fan-out]
    retry[Retries, queues, or leases]
    decision[Convergence or basin decisions]
    acceptance[Scientific acceptance]
    inferred[Inferred execution authority]

    executor --x batch
    executor --x parallel
    executor --x retry
    executor --x decision
    executor --x acceptance
    executor --x inferred
```
