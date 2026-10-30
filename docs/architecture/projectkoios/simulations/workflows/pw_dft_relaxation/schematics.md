# Plane-wave DFT relaxation workflow schematics

## Composition flow

```text
campaign ID + integration ID + neutral relaxation request
                             |
                             v
                  integration registry lookup
                             |
                             v
                    input projection wrapper
                             |
                             v
        projection + rendered filenames + external inputs
                             |
                             v
         separate-explicit-external-authority-required
```

## Intended workflow shape

```text
campaign -> projection_action -> input_projected
                                   |
                                   v
                       external_authority_required
                                   |
                                   v
                           terminal_outcome
```

This diagram is a name-level workflow-shape declaration, not an executable
Petri net: it does not encode arcs, guards, or token expressions. Any future
canonical CPN requires a separately reviewed WORKFLOWS contract and runtime.

## Authority boundary

```text
PwDftRelaxationComposer ----> deterministic projection and handoff
              |
              X----> calculator process, scheduler, or reusable authority
```

The cleaned `qe_projection.py` example follows the first edge only. Its
historical `execute_relaxation.py` source name remains in provenance, not in the
current example surface.

## Planned zero-pressure qualification flow

```text
exact starting structure
+ provisional numerical qualification Q_i@S_i
+ explicit cell mode, zero-pressure target, force/pressure policy
                         |
                         v
non-authorizing relaxation requirement
                         |
             separately admitted occurrence
                         |
                         v
normalized result + exact evidence
                         |
                         v
zero-pressure mechanical assessment
        |                |                 |
      passed           failed         inconclusive
        |
        v
exact mechanically qualified structure S_(i+1)
```

This planned flow is not implemented by the current projection handoff. Provider
completion and optimizer convergence are inputs to assessment, not substitutes
for normalized force, pressure, and cell-consistency checks.

Cross-stage composition performs fresh numerical confirmation on `S_(i+1)`. If
that confirmation selects a changed setting, it emits a new relaxation
requirement; no relaxation module or provider runner activates it automatically.

## Dependency direction

```text
outward tool / first-party adapter -> public relaxation integrations
            |                                  |
            v                                  v
pw_dft_relaxation workflow -> protected neutral relaxation contracts
```

The production workflow capability does not import outward tools, adapters,
examples, or integrations. Each provider process requires separate external
admission and authorization.
