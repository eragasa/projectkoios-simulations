# Relaxation workflow/CPN definition schematics

## Contract flow

`pw_dft_relaxation_workflow_definition()` declares application-owned places and transitions for campaign projection and external-authority handoff. It is an engine-neutral topology, not a generic runtime or CPN kernel.

```text
caller --> projectkoios.simulations.workflows.pw_dft_relaxation.workflow --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

No child documentation nodes; the index defines the complete local role.

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_relaxation.workflow` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
