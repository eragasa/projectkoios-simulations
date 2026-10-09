# PwDftScfConvergencePolicy schematics

## Contract flow

Fields: `tolerance_mev_per_atom`, `required_consecutive_deltas`, `mesh_increment`, `cutoff_increment_ev`, `extension_steps`, `maximum_mesh_density`, `maximum_cutoff_ev`, `maximum_grid_points`.

```text
caller --> PwDftScfConvergencePolicy --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

No child documentation nodes; the index defines the complete local role.

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.convergence.policy` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
