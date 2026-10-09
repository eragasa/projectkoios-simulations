# SCF terminal comparison schematics

## Contract flow

`PwDftScfEnergyAlignmentKind` distinguishes native from explicit reference-zero treatment. `PwDftScfComparisonInterpretation` bounds the resulting scientific claim. `PwDftScfEnergyAlignmentDeclaration` records policy before a result exists, and `PwDftScfEnergyAlignment` binds a result to that treatment. `PwDftScfComparisonRequest` orders two aligned results and cites input-alignment evidence. `PwDftScfComparator` produces an immutable `PwDftScfComparisonAnalysis`.

```text
caller --> projectkoios.simulations.workflows.pw_dft_scf.comparison --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

`PwDftScfComparator`, `PwDftScfComparisonAnalysis`, `PwDftScfComparisonInterpretation`, `PwDftScfComparisonRequest`, `PwDftScfEnergyAlignment`, `PwDftScfEnergyAlignmentDeclaration`, `PwDftScfEnergyAlignmentKind`

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.comparison` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
