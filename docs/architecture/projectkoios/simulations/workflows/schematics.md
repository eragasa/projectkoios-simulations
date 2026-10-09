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
  |    +-- engine-neutral Petri-net name inventory and facade
  |    `-- authoritative optional local SNAKES PetriNet
  |
  `-- pw_dft_relaxation
       +-- campaign and projection composition
       +-- external-authority-required handoff
       `-- projection/handoff workflow-shape name inventory
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

## Current Petri-net ownership and future extraction

```text
projectkoios.simulations.workflows today       WORKFLOWS after extraction
----------------------------------------       --------------------------
typed domain requests/actions/results   --->   runtime-neutral bindings
SCF SNAKES PetriNet topology            --->   extracted/compiled CPN plan
  places + transitions                         transition occurrences
  arcs + guards + token expressions            queues, leases, retries
bounded in-process firing                       cancellation and delivery
non-authorizing handoffs                        execution authority
```

The SCF `PetriNet` is authoritative today. `PwDftScfWorkflowDefinition` is a
conformance inventory of its names, not a second topology representation. There
is no reverse import from this package to a generic Workflow service or durable
runtime. The temporary SNAKES CPN is a bounded in-process engine adapter, not a
queue, scheduler, or authority service.

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
