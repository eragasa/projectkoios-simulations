# `VaspCalculationProjector`

The public `project` action reads `PwDftSimulation.settings.calculation_type` once and emits deterministic VASP INCAR controls:

| Calculation type | Generated assignments | Required inputs | Alignment |
|---|---|---|---|
| `scf` | `IBRION=-1`, `NSW=0` | None for calculation-mode projection | Conditional |
| `nscf` | `IBRION=-1`, `NSW=0`, `ICHARG=11` | Self-consistent `CHGCAR` | Conditional |
| `bands` | `IBRION=-1`, `NSW=0`, `ICHARG=11` | Self-consistent `CHGCAR`; band-path KPOINTS | Conditional |
| `relax` | `IBRION=2`, `ISIF=2` | `NSW` | Approximate |
| `md` | `IBRION=0` | `NSW`, `POTIM`, dynamics ensemble policy | Conditional |
| `vc-relax` | `IBRION=2`, `ISIF=3` | `NSW` | Approximate |
| `vc-md` | `IBRION=0`, `ISIF=3` | `NSW`, `POTIM`, variable-cell dynamics policy | Conditional |

No projection chooses an ionic-step budget, time step, thermostat, ensemble, prior-run artifact, or k-point path.
