# `projectkoios.integrations.vasp.calculation`

`VaspCalculationProjector` projects the one `CalculationType` selected in `PwDftSimulation.settings` into qualified `IncarAssignment` values. It returns a `VaspCalculationProjection` containing the generated `IncarFile`, its `AlignmentKind`, unresolved `required_inputs`, and a human-readable `qualification`.

The implementation follows the official VASP documentation retained as `IBRION_DOCUMENTATION_URL`, `ICHARG_DOCUMENTATION_URL`, `ISIF_DOCUMENTATION_URL`, and `NSW_DOCUMENTATION_URL`. It deliberately leaves budgets, dynamics policy, prior run artifacts, and band paths unresolved instead of inventing them.
