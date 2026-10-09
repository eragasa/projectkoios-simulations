# PwDftScfRecipe

Fields: `campaign_id`, `base_request`. `request_for` projects a convergence coordinate.

## Ownership boundary

This public `PwDftScfRecipe` contract mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/recipe.py` in `projectkoios.simulations.workflows.pw_dft_scf.recipe`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
