# `CalculationType`

Calculator-neutral string enumeration of seven plane-wave calculation modes. Quantum ESPRESSO accepts these serialized values directly in the 7.5 `&CONTROL` `calculation` variable; VASP requires conditional multi-field projections.

| Python member | QE value | Meaning |
|---|---|---|
| `CalculationType.scf` | `scf` | Self-consistent field calculation |
| `CalculationType.nscf` | `nscf` | Non-self-consistent field calculation |
| `CalculationType.bands` | `bands` | Band-structure calculation |
| `CalculationType.relax` | `relax` | Ionic relaxation |
| `CalculationType.md` | `md` | Molecular dynamics |
| `CalculationType.vc_relax` | `vc-relax` | Variable-cell ionic relaxation |
| `CalculationType.vc_md` | `vc-md` | Variable-cell molecular dynamics |

Python uses underscores in `vc_relax` and `vc_md`; their serialized values preserve the hyphens required by Quantum ESPRESSO.
