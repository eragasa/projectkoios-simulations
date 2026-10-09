# PwDftScfEnergyAlignment schematics

## Contract flow

- `result` is a completed, converged SCF result. - `kind` declares native or explicit-reference treatment. - `reference_energy_ev_per_atom` is subtracted from the native energy. - `reference_id` identifies external reference evidence. - `qualification` bounds interpretation of that reference. - `native_energy_ev_per_atom` exposes the unchanged observation. - `aligned_energy_ev_per_atom` exposes the explicitly adjusted value.

```text
caller --> PwDftScfEnergyAlignment --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

No child documentation nodes; the index defines the complete local role.

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.comparison` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
