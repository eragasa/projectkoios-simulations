# Workflow status

`PwDftScfWorkflowStatus` is a coarse projection of private workflow state.

## Ownership boundary

This package boundary mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/workflow/base.py` in `projectkoios.simulations.workflows.pw_dft_scf.workflow.base`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
