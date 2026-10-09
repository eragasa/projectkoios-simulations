# `PseudopotentialRepository`

`PseudopotentialRepository(entries)` is a frozen, slotted declaration of exact
local artifacts. `entries` must be an exact tuple whose members are exact
`PseudopotentialRepositoryEntry` values. Invalid containers or members raise
`TypeError`.

Construction derives an artifact identity from element symbol, filename,
SHA-256, and byte size. Those identities must be unique. Repeating an artifact
or declaring different scientific metadata for the same byte identity raises
`ValueError`; the repository cannot silently choose between conflicting
scientific declarations.

`resolve(required)` requires a `PseudopotentialFile` and matches the complete
record, including its scientific metadata. An undeclared requirement raises
`PseudopotentialNotFoundError`. The declared path must currently be a regular,
nonsymlink file; otherwise the same not-found error is raised. The method then
checks byte size followed by streamed SHA-256. A mismatch raises
`PseudopotentialIntegrityError`; an exact match returns the declared `Path`.

The repository does not search, download, substitute, or authorize execution.
Use [`PseudopotentialLibrary`](../PseudopotentialLibrary/index.md) only when the
caller needs deterministic discovery beneath an explicit deployment root.
