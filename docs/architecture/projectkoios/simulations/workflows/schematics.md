# `projectkoios.simulations.workflows` schematics

## Pure capability composition

```text
protected-core specification
            |
            v
typed request -> owner action or actionizer -> typed result
       ^                                          |
       |                                          v
provider-normalized evidence          execution-independent handoff
```

Each action performs one domain transformation. Owner source declarations may
state scientific topology and guards. A generic Workflow compiler translates
those declarations into canonical CPN places, transitions, and plans; the
generic runtime owns transition occurrences and lifecycle state.

## Runtime separation

```text
simulations.workflows source          generic Workflow compiler/runtime
----------------------------          ---------------------------------
scientific requests/results     --->  canonical CPN places/transitions/plans
source topology and guards      --->  compiled workflow definitions
comparison/convergence policy          occurrence identity and queueing
pure replay actions                    leases, retries, and reconciliation
execution handoff descriptions         cancellation and authority enforcement
```

Compilation points from owner declarations toward generic Workflow. This exact
namespace migration adds no Workflow dependency. A future compiler integration
may use stable runtime-neutral source or SDK contracts, but there is no import
edge from this layer to live service, kernel, scheduler, or runtime objects.

## Provider separation

```text
provider execution -> provider parsing -> normalized evidence
                                               |
                                               v
                                  simulations.workflows replay
```

Provider-native data does not cross directly into the workflow layer. Parsing,
normalization, mechanical execution evidence, and scientific assessment remain
separate operations with separate owners.
