# `PseudopotentialRepository`

Immutable repository with the public `entries` tuple. The public `resolve` action matches a required `PseudopotentialFile` by element, basename, byte size, and SHA-256, then verifies the declared regular nonsymlink file before returning its `Path`.
