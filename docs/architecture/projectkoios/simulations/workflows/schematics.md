# `projectkoios.simulations.workflows` schematics

## Layer map

```text
protected projectkoios.simulations core
  requests | results | settings | normalized observations | integrations IDs
                              |
                              v
projectkoios.simulations.workflows
  +-- pw_dft_scf
  |    +-- configuration and recipes
  |    +-- single-result comparison
  |    +-- convergence assessment/comparison/control/replay
  |    +-- engine-neutral topology and facade
  |    `-- optional local SNAKES CPN
  |
  `-- pw_dft_relaxation
       +-- campaign and projection composition
       +-- external-authority-required handoff
       `-- engine-neutral projection/handoff topology
```

The arrow points inward. Protected core modules never import the workflow
composition layer.

## SCF composition flow

```text
neutral SCF request
       |
       +--> single recipe ------------------------------+
       +--> k-point/cutoff/grid recipe -> coordinates --+--> child SCF results
                                                         |
normalized observations -> assessment -> controller ----+
                                                         |
successful results ------> qualified comparison          |
normalized replay evidence -> replay actionizer ---------+
                                                         v
                                             typed domain outcomes
```

Comparison never turns unlike calculator-native energy zeros into an
unqualified equivalence claim. Replay consumes normalized evidence rather than
provider artifacts.

## Relaxation composition flow

```text
neutral relaxation request + selected integration ID
                         |
                         v
               input projection wrapper
                         |
                         v
 projected inputs + required external inputs + non-authorizing handoff
```

The handoff states that separate explicit external authority is required. It
cannot start a calculator.

## Compiler/runtime separation

```text
simulation workflow owner                 generic Workflow owner
-------------------------                 ----------------------
requests, results, policies        --->   compiler input
source topology and guards         --->   canonical CPN plan
pure domain actions                       transition occurrences
scientific controller decisions           queues, leases, retries
non-authorizing handoffs                  cancellation and delivery
                                           execution authority
```

There is no reverse import from this package to a generic Workflow service or
durable runtime. The temporary local SNAKES CPN is a bounded in-process engine
adapter, not a queue, scheduler, or authority service.

## Tool and example boundary

```text
examples: declarations/data ---> repository tools ---> public integrations
          demonstrations              |                       |
                                      +-> local CPN            +-> projection/parsing
                                      +-> planning/comparison/visualization

repository tools --------X--------> calculator executable
```

The crossed edge is prohibited. Tools and examples remain outside wheel package
discovery and cannot convert an ordinary test or smoke invocation into
execution authority.
