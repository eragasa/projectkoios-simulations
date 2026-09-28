# `PseudopotentialRepository`

Immutable repository with the public `entries` tuple. The repository rejects conflicting scientific metadata declarations for the same artifact identity. The public `resolve` action matches the complete required `PseudopotentialFile`, including its scientific metadata and byte identity, then verifies the declared regular nonsymlink file's byte size and SHA-256 before returning its `Path`.
