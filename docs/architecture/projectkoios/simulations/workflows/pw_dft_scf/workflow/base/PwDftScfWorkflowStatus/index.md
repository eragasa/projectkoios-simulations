# PwDftScfWorkflowStatus

Values: `ready`, `awaiting_registration`, `awaiting_submission`, `waiting_for_completion`, `analyzing`, `terminated`.

## Ownership boundary

This public `PwDftScfWorkflowStatus` contract mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/workflow/base.py` in `projectkoios.simulations.workflows.pw_dft_scf.workflow.base`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
