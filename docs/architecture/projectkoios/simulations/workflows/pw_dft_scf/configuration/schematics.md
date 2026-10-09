# Plane-wave DFT SCF configuration schematics

## Contract flow

`PwDftScfRuntimeConfiguration` bounds internal progress. `PwDftScfCampaignConfiguration` binds a scientific recipe to a registered calculator integration.

```text
caller --> projectkoios.simulations.workflows.pw_dft_scf.configuration --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

`PwDftScfCampaignConfiguration`, `PwDftScfRuntimeConfiguration`

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.configuration` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
