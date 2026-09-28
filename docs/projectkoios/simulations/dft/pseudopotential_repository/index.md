# `projectkoios.simulations.dft.pseudopotential_repository`

`PseudopotentialRepository` resolves exact `PseudopotentialFile` requirements from explicit local `PseudopotentialRepositoryEntry` declarations. It rejects conflicting metadata declarations for the same artifact identity. Resolution matches the complete scientific metadata and file identity, then verifies expected size and SHA-256 before returning a path. `PseudopotentialNotFoundError` reports undeclared or unavailable artifacts; `PseudopotentialIntegrityError` reports changed bytes.

The repository never downloads pseudopotentials or searches undeclared filesystem locations.
