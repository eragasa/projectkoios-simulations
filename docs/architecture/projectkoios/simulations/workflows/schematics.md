# `projectkoios.simulations.workflows` schematics

## Layer map

```mermaid
flowchart TD
    core[Protected projectkoios.simulations core<br/>requests, settings, observations, evidence]
    workflows[projectkoios.simulations.workflows]

    subgraph scf[pw_dft_scf]
        scfConfig[Configuration and recipes]
        scfAssessment[Convergence assessment and replay]
        scfInventory[Engine-neutral name inventory]
        scfCpn[Authoritative optional SNAKES PetriNet]
    end

    subgraph relax[pw_dft_relaxation]
        relaxCampaign[Campaign and input composition]
        relaxHandoff[External-authority-required handoff]
        relaxInventory[Projection and handoff name inventory]
    end

    workflows --> scfConfig
    workflows --> relaxCampaign
    scfConfig --> scfAssessment --> scfInventory --> scfCpn
    relaxCampaign --> relaxHandoff --> relaxInventory
    scfConfig --> core
    relaxCampaign --> core
```

Allowed production dependencies point inward. The protected core never imports
the workflow composition layer.

## SCF composition flow

```mermaid
flowchart LR
    request[Neutral SCF request]
    single[Single recipe]
    convergence[K-point, cutoff, or grid recipe]
    coordinates[Child coordinates]
    child[Single-SCF child results]
    observations[Normalized observations]
    assessment[Convergence assessment]
    controller[Extend, criterion-satisfied, or budget outcome]
    comparison[Qualified comparison]
    replay[Normalized replay evidence]
    outcome[Typed domain outcomes]

    request --> single --> child
    request --> convergence --> coordinates --> child
    observations --> assessment --> controller --> outcome
    child --> comparison --> outcome
    replay --> outcome
```

Comparison does not treat unlike calculator-native absolute energy zeros as an
unqualified equivalence claim. Replay consumes normalized evidence rather than
provider artifacts.

## Relaxation composition flow

```mermaid
flowchart LR
    request[Neutral relaxation request]
    integration[Selected integration ID]
    projection[Input projection wrapper]
    prepared[CalculatorInputRecord]
    external[Required external inputs]
    handoff[Non-authorizing execution handoff]

    request --> projection
    integration --> projection
    projection --> prepared
    projection --> external
    prepared --> handoff
    external --> handoff
```

The handoff states that separate explicit external authority is required. It
cannot start a calculator.

## Chained-calculation boundary

```mermaid
sequenceDiagram
    participant C as Scientific parent workflow
    participant W as External Workflow runner
    participant E as Single-simulation executor

    C->>W: child requirement A
    C->>W: child requirement B
    C->>W: child requirement C
    W->>E: execute A
    E-->>W: terminal A evidence
    Note over W,E: concurrency one admits the next child only now
    W->>E: execute B
    E-->>W: terminal B evidence
    W->>E: execute C
    E-->>W: terminal C evidence
    W-->>C: ordered normalized child outcomes
```

The parent may enumerate convergence coordinates, reference phases, defect
starts, or supercell sizes. It never converts those children into one batch
calculator invocation. Retry and next-child admission remain runtime concerns;
convergence and basin decisions remain scientific composition.

## Current Petri-net ownership and future extraction

```mermaid
flowchart LR
    subgraph owner[projectkoios.simulations.workflows today]
        domain[Typed domain requests, actions, and results]
        net[SCF SNAKES PetriNet<br/>places, transitions, arcs, guards, expressions]
        local[Bounded in-process firing]
        handoffs[Non-authorizing handoffs]
    end

    subgraph runtime[Generic Workflow after reviewed extraction]
        binding[Runtime-neutral bindings]
        plan[Canonical compiled CPN plan]
        occurrences[Transition occurrences]
        lifecycle[Queues, leases, retries, cancellation, delivery]
        authority[Execution authority]
    end

    domain --> binding
    net --> plan
    local --> occurrences
    handoffs --> lifecycle
    handoffs --> authority
```

The SCF `PetriNet` is authoritative today. Its definition record is a
conformance inventory, not a second topology. The local adapter is not a queue,
scheduler, or authority service.

## Tool and example boundary

```mermaid
flowchart LR
    examples[Reviewed declarations and demonstrations]
    tools[Repository tools]
    cpn[Local optional CPN]
    integrations[Public provider integrations]
    calculator[Calculator executable]

    examples --> tools
    tools --> cpn
    tools --> integrations
    tools --x calculator
```

Tools and examples remain outside wheel package discovery and cannot convert an
ordinary test or smoke invocation into execution authority.
