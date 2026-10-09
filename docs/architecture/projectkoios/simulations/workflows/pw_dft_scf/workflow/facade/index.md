# Workflow façade

`PwDftScfWorkflowFacade` exposes actions, events, status, and terminal outcome without exposing a mutable engine marking.

## Ownership boundary

This package boundary mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/workflow/facade.py` in `projectkoios.simulations.workflows.pw_dft_scf.workflow.facade`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
