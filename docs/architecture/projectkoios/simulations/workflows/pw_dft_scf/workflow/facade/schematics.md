# Workflow façade schematics

## Contract flow

`PwDftScfWorkflowFacade` exposes actions, events, status, and terminal outcome without exposing a mutable engine marking.

```text
caller --> projectkoios.simulations.workflows.pw_dft_scf.workflow.facade --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

`PwDftScfWorkflowFacade`

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.workflow.facade` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
