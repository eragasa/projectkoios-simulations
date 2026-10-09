# Convergence controller values schematics

## Contract flow

`ExtendPwDftScfConvergence`, `PwDftScfConvergenceAccepted`, and `PwDftScfConvergenceBudgetExhausted` represent extension and terminal outcomes. `PwDftScfConvergenceController` routes assessments deterministically.

```text
caller --> projectkoios.simulations.workflows.pw_dft_scf.convergence.controller --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

`ExtendPwDftScfConvergence`, `PwDftScfConvergenceAccepted`, `PwDftScfConvergenceBudgetExhausted`, `PwDftScfConvergenceController`

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.convergence.controller` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
