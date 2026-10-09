# PwDftScfConvergenceComparisonRequest schematics

## Contract flow

Fields: `comparison_id`, `input_alignment_id`, `left`, and `right`. Both tests must use the same kind and policy and cite distinct evidence.

```text
caller --> PwDftScfConvergenceComparisonRequest --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

No child documentation nodes; the index defines the complete local role.

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.convergence.comparison` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
