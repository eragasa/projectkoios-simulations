# `projectkoios.integrations.vasp`

VASP-native integration boundary. It owns INCAR, KPOINTS, POSCAR, OUTCAR, and
[`vasprun.xml`](run_xml/index.md) representations together with
calculator-neutral calculation and SCF projections. [`calculation`](calculation/index.md)
projects one shared calculation mode into qualified INCAR assignments and
unresolved-input declarations. [Data-source composition](data/index.md) retains
execution and native artifact provenance separately, then presents SCF, NSCF,
[band-path](bands/index.md), and relaxation mode facades over those sources. The package does not select
pseudopotentials, authorize execution, or claim that projected inputs are
runnable, converged, or scientifically accepted.
