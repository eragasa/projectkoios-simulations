# Plane-wave DFT SCF recipes schematics

## Contract flow

`PwDftScfRecipe`, `PwDftScfSingleCalculationRecipe`,
`PwDftScfKpointConvergenceRecipe`, `PwDftScfCutoffConvergenceRecipe`, and
`PwDftScfGridConvergenceRecipe` cover the four currently implemented scientific
modes.

```text
caller --> projectkoios.simulations.workflows.pw_dft_scf.recipe --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

Current convergence projection is:

```text
exact base SCF request
  + cubic mesh-density axis
  + wavefunction-cutoff axis
  -> immutable child requests
```

Bulk qualification reuses that projection unchanged:

```text
exact seed-bound SCF request
  + existing cubic mesh and wavefunction-cutoff candidates
  + neutral coupled-cutoff realization
  -> immutable child requests
  -> typed correlation binds projected input, occurrence, evidence, and adapter mapping
```

Recipe projection remains non-authorizing and does not convert a result on one
structure into a qualification for another. No second coordinate shape is
required for the first route.

## Documented children

`PwDftScfCutoffConvergenceRecipe`, `PwDftScfGridConvergenceRecipe`, `PwDftScfKpointConvergenceRecipe`, `PwDftScfRecipe`, `PwDftScfSingleCalculationRecipe`

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.recipe` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
