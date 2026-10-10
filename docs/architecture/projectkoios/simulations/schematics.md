# `projectkoios.simulations` schematics

## Dependency direction

```mermaid
flowchart TD
    downstream[Downstream application or domain composition]
    workflows[simulations.workflows]
    integrations[integrations and adapters]
    core[Protected simulations core]
    declarations[Owner source declarations]
    compiler[External compiler binding]
    generic[Generic Workflow]

    downstream --> workflows --> core
    downstream --> integrations --> core
    downstream --> core
    declarations --> compiler --> generic
```

Allowed production dependencies point inward toward the protected core.
Downstream composition may use public workflow and integration contracts, but
production workflow modules do not import provider implementations and
production integration modules do not own workflow policy.

## Forbidden reverse dependencies

```mermaid
flowchart LR
    core[Protected core]
    workflows[simulations.workflows]
    integrations[Integrations and adapters]
    applications[Downstream applications]
    runtime[Live Workflow runtime]

    core --x workflows
    core --x integrations
    workflows --x integrations
    workflows --x applications
    workflows --x runtime
    applications --x runtime
```

A live-runtime integration crosses a separately reviewed binding or process
boundary. A stable runtime-neutral source or SDK contract remains a distinct
compiler-integration decision.

## Namespace transition

```mermaid
flowchart LR
    historical[projectkoios.simulation_workflows<br/>historical source]
    current[projectkoios.simulations.workflows<br/>current owner]

    historical -->|atomic forward move| current
```

The old and new production trees do not coexist. No import alias, re-export,
compatibility package, or namespace shim bridges them.

## Specification and evidence flow

```mermaid
flowchart TD
    structure[Exact StructureRecord]
    simulation[Exact SimulationRecord]
    input[CalculatorInputRecord<br/>created by outward translation]
    authority[Separate explicit execution authority]
    execution[One authorized calculator execution]
    evidence[SimulationEvidenceRecord]
    compatibility[simulations.dft.defects compatibility]
    arithmetic[simulations.defects arithmetic]
    publication[Explicit relaxed-structure publication]

    structure --> simulation --> input --> authority --> execution --> evidence
    evidence --> compatibility --> arithmetic
    evidence --> publication
```

Generic defect equations do not depend on the DFT binding. The binding supplies
one method-qualified evidence path.

## Authority and single-execution flow

```mermaid
sequenceDiagram
    participant C as Scientific composition
    participant W as External Workflow runtime
    participant E as CalculatorExecutor
    participant P as Calculator process
    participant A as Retained artifacts

    C->>W: pure child requirement or handoff
    W->>W: require explicit execution authority
    W->>E: one CalculatorExecutionRequest
    E->>P: start one synchronous subprocess
    loop native output
        P-->>E: output bytes
        E-->>W: live operational output
        E->>A: retain identical native bytes
    end
    P-->>E: terminal status
    E->>A: write execution.json
    E-->>W: terminal execution record
    W-->>C: normalized immutable evidence
```

A handoff describes required work; it does not authorize or start a calculator.
An external runtime configured with concurrency one waits for the terminal
record before admitting another occurrence. Live console output is operational
observability, not evidence, acceptance, or authority.
