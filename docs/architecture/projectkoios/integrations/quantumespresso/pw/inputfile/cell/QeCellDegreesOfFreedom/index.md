# `QeCellDegreesOfFreedom`

These values come from Quantum ESPRESSO 7.5's `pw.x` input description for
[`&CELL.cell_dofree`](https://www.quantum-espresso.org/Doc/INPUT_PW.html#cell_dofree).
The corresponding release source is `PW/Doc/INPUT_PW.def` under
`var cell_dofree`; the runtime interpretation is implemented by
`Modules/cell_base.f90` in `init_dofree`.

| Python enum | Native `cell_dofree` value | QE 7.5 meaning |
| --- | --- | --- |
| `ALL` | `all` | Move all lattice axes and angles |
| `IBRAV` | `ibrav` | Preserve constraints implied by the initial Bravais lattice |
| `A` | `a` | Fix the x component of axis 1 |
| `B` | `b` | Fix the y component of axis 2 |
| `C` | `c` | Fix the z component of axis 3 |
| `FIX_A` | `fixa` | Fix axis 1 |
| `FIX_B` | `fixb` | Fix axis 2 |
| `FIX_C` | `fixc` | Fix axis 3 |
| `X` | `x` | Move only the x component of axis 1 |
| `Y` | `y` | Move only the y component of axis 2 |
| `Z` | `z` | Move only the z component of axis 3 |
| `XY` | `xy` | Move only axis-1 x and axis-2 y components |
| `XZ` | `xz` | Move only axis-1 x and axis-3 z components |
| `YZ` | `yz` | Move only axis-2 y and axis-3 z components |
| `XYZ` | `xyz` | Move only the three corresponding diagonal components |
| `SHAPE` | `shape` | Change axes and angles while preserving volume |
| `VOLUME` | `volume` | Change volume while preserving angles |
| `TWO_DIMENSIONAL_XY` | `2Dxy` | Allow only x and y components to change |
| `TWO_DIMENSIONAL_SHAPE` | `2Dshape` | As `2Dxy`, while preserving xy area |
| `EPITAXIAL_AB` | `epitaxial_ab` | Fix axes 1 and 2; allow axis 3 to move |
| `EPITAXIAL_AC` | `epitaxial_ac` | Fix axes 1 and 3; allow axis 2 to move |
| `EPITAXIAL_BC` | `epitaxial_bc` | Fix axes 2 and 3; allow axis 1 to move |

This enum contains the documented base spellings only. Quantum ESPRESSO also
documents compound `ibrav+option` syntax; the maintained adapter does not model
those compound strings. Its generated input uses `ibrav = 0`, so the
`vc-relax` projector rejects the base `ibrav` value rather than emitting an
ineffective constraint.

Quantum ESPRESSO warns that some constraints are unsuitable for nonorthogonal
cells and can break symmetry. Inclusion here means that the native spelling is
represented; it is not a scientific suitability or convergence claim.
