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

## Owner topology

```text
campaign -> projection_action -> input_projected
                                   |
                                   v
                       external_authority_required
                                   |
                                   v
                           terminal_outcome
```

The topology is an owner source declaration. A generic Workflow compiler owns
canonical CPN places and transitions; a generic runtime owns occurrence and
lifecycle state.

## Authority boundary

```text
PwDftRelaxationComposer ----> deterministic projection and handoff
              |
              X----> calculator process, scheduler, or reusable authority
```

The cleaned `qe_projection.py` example follows the first edge only. Its
historical `execute_relaxation.py` source name remains in provenance, not in the
current example surface.

## Dependency direction

```text
QE example composition -> public QE relaxation integration
            |                         |
            v                         v
pw_dft_relaxation workflow -> protected neutral relaxation contracts
```

The production workflow capability does not import the QE example or outward
integration.
