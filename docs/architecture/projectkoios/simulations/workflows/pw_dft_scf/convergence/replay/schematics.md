# PW-DFT SCF convergence replay schematics

## Contract flow

`PwDftScfConvergenceReplayActionizer` owns deterministic application-policy replay over `PwDftScfConvergenceReplayEvidence`. The evidence contract carries normalized energy observations, provider identity, source-evidence reference, and the bounded application policy. Native parser behavior and raw artifacts remain in the provider owner.

```text
caller --> projectkoios.simulations.workflows.pw_dft_scf.convergence.replay --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

No child documentation nodes; the index defines the complete local role.

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.convergence.replay` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
