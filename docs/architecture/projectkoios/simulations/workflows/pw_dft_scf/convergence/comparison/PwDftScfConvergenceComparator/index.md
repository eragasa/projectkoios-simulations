# PwDftScfConvergenceComparator

`compare` reassesses two like-for-like convergence tests and reports descriptive differences without asserting calculator or basis equivalence.

## Ownership boundary

This public `PwDftScfConvergenceComparator` contract mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/convergence/comparison.py` in `projectkoios.simulations.workflows.pw_dft_scf.convergence.comparison`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
