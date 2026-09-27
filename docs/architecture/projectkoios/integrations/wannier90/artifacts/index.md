# Artifact identity and correlation

`Wannier90NativeArtifact` retains an exact basename-like logical name and an
immutable byte payload. Its identity is the tuple `(name, byte_count, sha256)`.
`Wannier90NativeArtifactCorrelator` rejects duplicate names, missing or extra
names, byte-count differences, and digest differences, then returns expected
and observed identities in expected order as explicit correlation evidence.

Correlation authenticates caller-supplied bytes only. It does not prove that a
payload came from Wannier90 or that its scientific contents are valid.

`Wannier90NativeArtifactSetParser` requires exact seed-derived names for all
seven supported files. Parsing is in-memory and does not discover or open
paths. The returned `Wannier90ParsedNativeArtifactSet` enforces agreement of:

- k-point counts across `.eig`, `.amn`, `.mmn`, `.nnkp`, and `_u.mat`;
- band counts across `.eig`, `.amn`, `.mmn`, and `_u.mat`; and
- Wannier counts across `.amn`, `.wout`, `_u.mat`, and `_hr.dat`.

Authentication and parsing remain explicit steps so a caller can retain the
correlation result alongside the parsed set.
