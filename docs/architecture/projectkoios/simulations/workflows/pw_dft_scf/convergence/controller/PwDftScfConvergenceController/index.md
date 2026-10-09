# PwDftScfConvergenceController

`decide` routes one assessment to extension, acceptance, or budget exhaustion.

## Ownership boundary

This public `PwDftScfConvergenceController` contract mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/convergence/controller.py` in `projectkoios.simulations.workflows.pw_dft_scf.convergence.controller`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
