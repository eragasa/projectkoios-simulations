# `PoscarModel`

Immutable POSCAR model with public `comment` and `unit_cell_model` fields. The public `write` action requires a `PoscarWriter` and delegates atomic filesystem serialization to that writer.
