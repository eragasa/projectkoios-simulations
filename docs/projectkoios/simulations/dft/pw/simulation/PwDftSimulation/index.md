# `PwDftSimulation`

Immutable plane-wave DFT simulation root with public `unit_cell` and `settings` fields. `unit_cell` retains one exact `physkit.periodic.unit_cell.UnitCell`; calculator input models receive that same object rather than reconstructing independent structures. `settings` retains one `PwDftSettings` selected once for projection through calculator adapters.
