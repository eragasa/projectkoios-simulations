# PwDftScfComparator schematics

## Contract flow

`compare` performs a pure ordered comparison after both child SCF workflows have produced successful terminal results. It emits no calculator effect and makes no unqualified equivalence claim.

```text
caller --> PwDftScfComparator --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

No child documentation nodes; the index defines the complete local role.

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.comparison` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
