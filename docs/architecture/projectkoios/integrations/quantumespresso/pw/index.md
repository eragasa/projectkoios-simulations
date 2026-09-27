# `pw`

This package owns integration behavior specific to Quantum ESPRESSO `pw.x`.
Input-file components are defined under `inputfile`; calculation-mode packages
consume those components without redefining them. The package also owns the
`pw.x` simulation bundle and execution boundary. SCF, NSCF, `relax`, and
`vc_relax` each own a `data_extraction` unit. Only exact-artifact and captured-
stream behavior demonstrated common across those units is factored into the
`pw.data_extraction` base.
