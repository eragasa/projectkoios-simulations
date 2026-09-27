# `ibrav`

Typed representation of Quantum ESPRESSO 7.5 `ibrav`, `celldm`, conventional lattice parameters, and `CELL_PARAMETERS` compatibility rules through `QeBravaisLattice`, `QeCellParametersUnit`, `QeCelldm`, `QeLatticeParameters`, `QeCellParameters`, and `QeIbrav`.

`QE_PW_INPUT_AUTHORITY` records the governing syntax authority.

Authority: <https://www.quantum-espresso.org/Doc/INPUT_PW.html#id1>

The module enforces parameter-family exclusivity and explicit cell requirements. It records coordinate precision but does not invent a universal minimum for QE's system-dependent requirement that `ibrav=0` vectors retain sufficient digits and exact symmetry.
