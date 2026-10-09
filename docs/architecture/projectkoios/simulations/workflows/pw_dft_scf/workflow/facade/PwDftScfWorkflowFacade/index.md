# PwDftScfWorkflowFacade

Methods: `pending_actions`, `accept`, `status`, `outcome`.

## Ownership boundary

This public `PwDftScfWorkflowFacade` contract mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/workflow/facade.py` in `projectkoios.simulations.workflows.pw_dft_scf.workflow.facade`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
