# PwDftScfConvergenceAssessment

Fields: `converged`, `can_extend`, `kpoint_tail_deltas_mev_per_atom`, `cutoff_tail_deltas_mev_per_atom`, `requested_points`, `reason`.

## Ownership boundary

This public `PwDftScfConvergenceAssessment` contract mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/convergence/base.py` in `projectkoios.simulations.workflows.pw_dft_scf.convergence.base`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
