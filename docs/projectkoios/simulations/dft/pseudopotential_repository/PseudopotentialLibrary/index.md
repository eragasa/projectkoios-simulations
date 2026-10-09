# `PseudopotentialLibrary`

## Purpose

`PseudopotentialLibrary(root: Path)` is an immutable deployment resolver for
caller-selected `PseudopotentialFile` requirements. It discovers where exact
required bytes are installed beneath one explicit local root. It does not choose
scientific metadata, infer a family from an element, download files, or grant
calculator authority.

## Construction contract

`root` must satisfy all of the following, in validation order:

1. it is a `pathlib.Path`, otherwise construction raises `TypeError`;
2. it is absolute and its path parts contain no `..`, otherwise construction
   raises `ValueError`; and
3. it names an existing directory and is not itself a symlink, otherwise
   construction raises `ValueError`.

The record is frozen and slotted. Construction validates the deployment root at
that instant; it does not cache directory contents.

## `resolve(required)`

`required` must be a `PseudopotentialFile`, otherwise `TypeError` is raised. Its
`filename` is already constrained by that type to be a basename.

Resolution performs these deterministic steps:

1. recursively enumerate entries beneath `root` having exactly the required
   basename;
2. sort candidate paths;
3. reject a candidate that is a symlink, is not a regular file, or resolves
   outside the configured root;
4. compare its current byte size with `required.byte_size`;
5. stream and compare its complete SHA-256 with `required.sha256`; and
6. return the first sorted candidate satisfying every byte-identity check.

Scientific fields such as element, exchange-correlation approximation,
formalism, relativistic treatment, and valence-electron count are not search
criteria. The caller has already selected those fields by supplying the complete
requirement. The library only binds that requirement to identical bytes.

If multiple files contain the same required bytes, the lexicographically first
sorted path is returned. This is deterministic deployment resolution, not
scientific preference.

### Resolution failures

| Condition | Result |
|---|---|
| No entry with the required basename exists beneath the root | `PseudopotentialNotFoundError` |
| One or more same-named entries exist, but none passes type, containment, size, and SHA-256 checks | `PseudopotentialIntegrityError` |
| The required value is not a `PseudopotentialFile` | `TypeError` |
| A candidate disappears or becomes unreadable during inspection | The underlying filesystem exception propagates |

The method does not suppress filesystem races. Consumers requiring a stable
artifact should immediately construct and retain the exact repository entry;
`PseudopotentialRepository.resolve()` verifies the bytes again when consumed.

## `build_repository(required)`

`required` must be an exact tuple of `PseudopotentialFile` values. A list or any
other container raises `TypeError`; a tuple containing another value also raises
`TypeError`.

The method resolves requirements in caller order and returns
`PseudopotentialRepository(entries=...)`. An empty tuple produces an empty
repository. Repeated or metadata-conflicting declarations for the same artifact
identity are rejected by `PseudopotentialRepository` as non-unique.

## Example

```python
from pathlib import Path

from projectkoios.simulations.dft.pseudopotential_repository import (
    PseudopotentialLibrary,
)

# `required_file` is a fully specified PseudopotentialFile selected elsewhere.
library = PseudopotentialLibrary(Path("/opt/pseudopotentials/quantum-espresso"))
path = library.resolve(required_file)
repository = library.build_repository((required_file,))
assert repository.resolve(required_file) == path
```

Creating the library, resolving a path, or building a repository does not run a
calculator and does not constitute execution authorization.
