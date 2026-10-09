# PwDftScfSingleCalculationRecipe

One calculation with no parameter convergence.

## Ownership boundary

This public `PwDftScfSingleCalculationRecipe` contract mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/recipe.py` in `projectkoios.simulations.workflows.pw_dft_scf.recipe`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
