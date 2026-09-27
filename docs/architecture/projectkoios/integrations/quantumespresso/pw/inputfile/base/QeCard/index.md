# `QeCard`

Nominal immutable base with ordered `lines` and an optional `option`. The derived
`kind` and `tag` identify the QE group. `implemented` reports whether maintained
semantic support exists. `to_input_group` projects supported components into the
lexical input model and raises `NotImplementedError` for declared placeholders.
