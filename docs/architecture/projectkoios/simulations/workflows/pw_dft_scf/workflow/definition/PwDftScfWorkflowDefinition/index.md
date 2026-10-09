# PwDftScfWorkflowDefinition

Fields: `name`, `places`, `transitions`. These fields inventory the authoritative
SNAKES Petri net; they do not define or replace its arcs, guards, or token
expressions.

## Ownership boundary

This public `PwDftScfWorkflowDefinition` contract mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/workflow/definition.py` in `projectkoios.simulations.workflows.pw_dft_scf.workflow.definition`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
