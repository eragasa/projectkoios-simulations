# Relaxation composition schematics

## Contract flow

- `PwDftRelaxationCampaign` binds application identity, integration identity,   and a neutral `PwDftRelaxationRequest`. - `PwDftRelaxationComposer` selects a registered public projection integration. - `PwDftRelaxationCompositionResult` returns projected native input text and a   non-authorizing external handoff. - `PwDftRelaxationExecutionHandoff` cannot represent execution approval.

```text
caller --> projectkoios.simulations.workflows.pw_dft_relaxation.composition --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

No child documentation nodes; the index defines the complete local role.

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_relaxation.composition` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
