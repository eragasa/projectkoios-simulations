# Plane-wave DFT SCF recipes schematics

## Contract flow

`PwDftScfRecipe`, `PwDftScfSingleCalculationRecipe`, `PwDftScfKpointConvergenceRecipe`, `PwDftScfCutoffConvergenceRecipe`, and `PwDftScfGridConvergenceRecipe` cover the four supported scientific modes.

```text
caller --> projectkoios.simulations.workflows.pw_dft_scf.recipe --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

`PwDftScfCutoffConvergenceRecipe`, `PwDftScfGridConvergenceRecipe`, `PwDftScfKpointConvergenceRecipe`, `PwDftScfRecipe`, `PwDftScfSingleCalculationRecipe`

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.recipe` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
