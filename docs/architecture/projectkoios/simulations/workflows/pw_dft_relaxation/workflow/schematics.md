# Relaxation workflow-shape definition schematics

## Contract flow

`pw_dft_relaxation_workflow_definition()` inventories intended place and transition names for campaign projection and external-authority handoff. It does not encode executable arcs, guards, or token expressions.

```text
caller --> projectkoios.simulations.workflows.pw_dft_relaxation.workflow --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

No child documentation nodes; the index defines the complete local role.

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_relaxation.workflow` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Any executable relaxation CPN requires a separately reviewed WORKFLOWS contract.
