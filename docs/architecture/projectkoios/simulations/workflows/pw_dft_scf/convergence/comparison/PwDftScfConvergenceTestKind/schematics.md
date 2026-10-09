# PwDftScfConvergenceTestKind schematics

## Contract flow

Members: `K_POINTS`, `WAVEFUNCTION_CUTOFF`, and joint `CROSS`.

```text
caller --> PwDftScfConvergenceTestKind --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

No child documentation nodes; the index defines the complete local role.

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.convergence.comparison` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
