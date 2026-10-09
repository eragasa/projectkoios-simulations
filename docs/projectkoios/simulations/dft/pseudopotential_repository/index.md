# `projectkoios.simulations.dft.pseudopotential_repository`

`PseudopotentialLibrary` discovers exact `PseudopotentialFile` requirements beneath one explicitly configured local root. It matches the required basename, byte size, and complete SHA-256 rather than selecting by element or whichever filename appears first. Duplicate materializations of the same exact bytes are resolved deterministically.

`PseudopotentialRepository` resolves exact requirements from explicit `PseudopotentialRepositoryEntry` declarations. It rejects conflicting metadata declarations for the same artifact identity. Resolution matches the complete scientific metadata and file identity, then verifies expected size and SHA-256 before returning a path. `PseudopotentialNotFoundError` reports undeclared or unavailable artifacts; `PseudopotentialIntegrityError` reports changed or same-named nonmatching bytes.

Neither object downloads pseudopotentials, chooses a scientific family, substitutes a same-element artifact, or authorizes calculator execution.
