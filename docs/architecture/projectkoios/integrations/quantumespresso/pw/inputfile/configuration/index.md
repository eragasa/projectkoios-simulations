# `inputfile.configuration`

`QeRelaxationInputConfiguration` validates fields shared by fixed- and
variable-cell calculator-input translation. This includes the QE-native
`electronic_tolerance_ry` and the distinct Ry-valued `electronic_atol_ry` used
only for conversion comparison.

See the [relaxation translation numeric contract](../../relaxation/projection/numeric.md)
for their separate meanings.
