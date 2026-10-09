# Workflow status schematics

## Contract flow

`PwDftScfWorkflowStatus` is a coarse projection of private workflow state.

```text
caller --> projectkoios.simulations.workflows.pw_dft_scf.workflow.base --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

`PwDftScfWorkflowStatus`

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.workflow.base` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
