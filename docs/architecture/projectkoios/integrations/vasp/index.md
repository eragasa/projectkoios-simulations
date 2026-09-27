# `projectkoios.integrations.vasp`

VASP-native integration boundary. It owns INCAR, KPOINTS, POSCAR, and OUTCAR representations together with calculator-neutral calculation and SCF projections. [`calculation`](calculation/index.md) projects one shared calculation mode into qualified INCAR assignments and unresolved-input declarations. The package does not select pseudopotentials, authorize execution, or claim that projected inputs are runnable or scientifically converged.
