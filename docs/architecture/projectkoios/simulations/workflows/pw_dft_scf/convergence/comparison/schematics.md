# SCF convergence comparison schematics

## Contract flow

`PwDftScfConvergenceTestKind` identifies k-point, cutoff, and cross tests. `PwDftScfConvergenceComparisonInterpretation` bounds claims. `PwDftScfConvergenceTest` binds observations to policy and evidence. `PwDftScfConvergenceComparisonRequest` orders two tests. `PwDftScfConvergenceComparator` produces `PwDftScfConvergenceComparisonAnalysis` by recomputing each assessment under one shared policy without comparing calculator-native absolute energy zeros.

```text
caller --> projectkoios.simulations.workflows.pw_dft_scf.convergence.comparison --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

`PwDftScfConvergenceComparator`, `PwDftScfConvergenceComparisonAnalysis`, `PwDftScfConvergenceComparisonInterpretation`, `PwDftScfConvergenceComparisonRequest`, `PwDftScfConvergenceTest`, `PwDftScfConvergenceTestKind`

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.convergence.comparison` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
