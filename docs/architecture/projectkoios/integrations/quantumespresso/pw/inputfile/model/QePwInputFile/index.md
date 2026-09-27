# `QePwInputFile`

Immutable typed Quantum ESPRESSO input composition with public `control_block`, `unit_cell`, and `groups` fields. `unit_cell` is the exact shared `UnitCell` from `PwDftSimulation`. `control_block` is rendered first as `&CONTROL`; lexical `groups` may not duplicate that namelist. The remaining groups stay lexical, and agreement between existing structural card text and the represented unit cell is not yet inferred or claimed.
