# Workflow definition

`PwDftScfWorkflowDefinition` inventories the fixed lifecycle names.
`pw_dft_scf_workflow_definition()` constructs that detached inventory; the
complete executable topology remains authoritative in `pw_dft_scf.cpn.net`.

## Ownership boundary

This package boundary mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/workflow/definition.py` in `projectkoios.simulations.workflows.pw_dft_scf.workflow.definition`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
