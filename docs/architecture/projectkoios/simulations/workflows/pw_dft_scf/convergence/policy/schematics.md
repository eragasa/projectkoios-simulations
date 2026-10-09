# Convergence policy schematics

## Contract flow

`PwDftScfConvergencePolicy` bounds tolerance, neighboring increments, axis maxima, extension size, and total grid points.

```text
caller --> projectkoios.simulations.workflows.pw_dft_scf.convergence.policy --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

`PwDftScfConvergencePolicy`

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.convergence.policy` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
