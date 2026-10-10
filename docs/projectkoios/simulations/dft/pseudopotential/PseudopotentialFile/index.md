# `PseudopotentialFile`

Immutable binding from a `pseudopotential` to an explicit
`PseudopotentialArtifactFormat`, optional format version, basename `filename`,
lowercase hexadecimal `sha256`, and positive `byte_size`. UPF artifacts require
an explicit format version. The read-only `symbol` property returns the bound
pseudopotential's element symbol.

The record does not read, copy, download, redistribute, or authenticate external bytes.
