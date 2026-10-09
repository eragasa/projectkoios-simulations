# PwDftScfGridConvergenceRecipe

Fields: `mesh_densities`, `wavefunction_cutoffs_ev`, `policy`. `coordinates` returns the initial grid.

## Ownership boundary

This public `PwDftScfGridConvergenceRecipe` contract mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/recipe.py` in `projectkoios.simulations.workflows.pw_dft_scf.recipe`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
