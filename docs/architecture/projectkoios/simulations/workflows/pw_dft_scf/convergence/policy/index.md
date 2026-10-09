# Convergence policy

`PwDftScfConvergencePolicy` bounds tolerance, neighboring increments, axis maxima, extension size, and total grid points.

## Ownership boundary

This package boundary mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/convergence/policy.py` in `projectkoios.simulations.workflows.pw_dft_scf.convergence.policy`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
