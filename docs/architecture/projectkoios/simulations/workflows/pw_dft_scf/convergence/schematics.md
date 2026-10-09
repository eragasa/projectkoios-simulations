# Plane-wave DFT SCF convergence schematics

## Contract flow

Calculator-neutral axis and grid convergence models, policy, assessment, controller outcomes, and qualified cross-backend convergence-test comparison.

```text
caller --> projectkoios.simulations.workflows.pw_dft_scf.convergence --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

`assessment`, `base`, `comparison`, `controller`, `policy`, `replay`

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.convergence` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
