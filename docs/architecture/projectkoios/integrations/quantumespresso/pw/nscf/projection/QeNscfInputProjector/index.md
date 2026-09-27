# `QeNscfInputProjector`

`configuration` supplies explicit QE-native NSCF policy. `project` accepts a
`PwDftSimulation` whose calculation type is `nscf` and renders one input with
explicit `nbnd`, fixed occupations, disabled symmetry reduction, and
source-ordered `K_POINTS crystal` values.
