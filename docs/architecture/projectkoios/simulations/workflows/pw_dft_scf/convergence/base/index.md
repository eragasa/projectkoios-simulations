# Convergence values

`PwDftScfConvergenceAxis`, `PwDftScfConvergenceCoordinate`, `PwDftScfEnergyObservation`, and `PwDftScfConvergenceAssessment` preserve normalized convergence evidence.

## Ownership boundary

This package boundary mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/convergence/base.py` in `projectkoios.simulations.workflows.pw_dft_scf.convergence.base`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
