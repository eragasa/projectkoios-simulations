# EnergyGridConvergenceAssessor

`assess` evaluates both high-coordinate grid edges.

## Ownership boundary

This public `EnergyGridConvergenceAssessor` contract mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/convergence/assessment.py` in `projectkoios.simulations.workflows.pw_dft_scf.convergence.assessment`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
