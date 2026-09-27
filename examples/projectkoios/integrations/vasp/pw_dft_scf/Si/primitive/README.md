# Silicon VASP single-SCF integration

This directory retains a static VASP-native projection for a primitive-silicon
SCF calculation. The rendered `INCAR`, `KPOINTS`, `POSCAR`, and
`input-projection.json` files are inspection examples; this repository does not
include an application runner that regenerates or executes them.

The retained
[`negative-lattice-orientation`](evidence/failures/negative-lattice-orientation/README.md)
failure demonstrates that a zero process return code does not imply calculator
or workflow success. It is failure evidence, not a successful reference result,
numerical verification, or scientific validation.

Application-layer campaign and convergence declarations are intentionally not
part of this provider example. They are routed to the `projectkoios.applications`
composition owner in the `projectkoios-applications` repository. `pw_dft_scf`
is one composable capability there, not a standalone application.
