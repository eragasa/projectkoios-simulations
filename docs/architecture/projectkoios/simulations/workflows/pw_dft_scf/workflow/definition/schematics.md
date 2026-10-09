# Workflow definition schematics

## Contract flow

`PwDftScfWorkflowDefinition` names the fixed lifecycle. `pw_dft_scf_workflow_definition` constructs it.

```text
caller --> projectkoios.simulations.workflows.pw_dft_scf.workflow.definition --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

`PwDftScfWorkflowDefinition`

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.workflow.definition` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
