# Plane-wave DFT SCF convergence

Calculator-neutral axis and grid convergence models, policy, assessment,
controller outcomes, and qualified cross-backend convergence-test comparison.

## Current scope and bulk reuse

The implemented energy observation binds one cubic mesh/wavefunction-cutoff
coordinate to total energy per atom. The grid assessor evaluates the two
high-coordinate edges, and the controller extends, accepts, or reports budget
exhaustion. This is the convergence implementation reused by bulk
qualification.

Current observations and assessments do not carry those identities. A new typed
correlation binds them to exact structure, request/specification, neutral cutoff
realization, full sampling policy, prepared input, selected occurrence,
normalized evidence bytes, artifacts, pseudopotentials, and adapter mapping.
Confirmation reruns the existing assessment on the relaxed structure and creates
a fresh correlation. If the selected highest tested corner changes, cross-stage
composition—not this assessor—requires re-relaxation and fresh confirmation. No
generalized convergence coordinate is required for the first route.

This package continues to own reusable assessment and controller semantics. The
planned
[`pw_dft_bulk_qualification`](../../pw_dft_bulk_qualification/index.md) package
owns the cross-stage feedback and stable structure/setting-pair decision.

## Ownership boundary

This package boundary mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/convergence/__init__.py` in `projectkoios.simulations.workflows.pw_dft_scf.convergence`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
