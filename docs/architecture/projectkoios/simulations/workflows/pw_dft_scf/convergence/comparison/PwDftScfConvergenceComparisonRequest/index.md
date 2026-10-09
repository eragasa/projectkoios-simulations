# PwDftScfConvergenceComparisonRequest

Fields: `comparison_id`, `input_alignment_id`, `left`, and `right`. Both tests must use the same kind and policy and cite distinct evidence.

## Ownership boundary

This public `PwDftScfConvergenceComparisonRequest` contract mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/convergence/comparison.py` in `projectkoios.simulations.workflows.pw_dft_scf.convergence.comparison`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
