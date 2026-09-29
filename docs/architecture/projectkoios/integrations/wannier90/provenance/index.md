# Provenance and limits

The parser source is bound to `ksdft2effmass` commit
`7bd913151f7e61ed2bdba593df920be36573b502`, root tree
`4f7ca69afbd1381c0cb736b0efe6b8ac5431acf6`, implementation subtree
`1b5c6cd4a46f2fe70859c3aa1fded938a497e4dc`, and test subtree
`e5093059c62650e2afe14dccd80f25544e05c1df`. The donor Apache-2.0 text has
SHA-256 `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`
and is byte-identical to this repository's `LICENSE`.

The installed distribution includes the machine-readable `provenance.json`
resource in `projectkoios.integrations.wannier90`. The
[static transitive import closure](import-closure.md) records both semantic and
incidental package-facade dependencies. The only semantic in-repository
dependency was the donor quantity module, blob
`d98be473e19e17a59563fc7c3e00cca02fd822d3`. Generic quantity ownership is
`projectkoios-physkit`, so the extraction depends on the current compatible
`projectkoios-physkit>=0.1.0` distribution and imports
`projectkoios.physkit.units.quantities` instead of copying it here. Commit
`97032f16c9125aa124750508f8513cca9f6dab02` identifies the implementation
reviewed during extraction, not an installation pin.

## Residual scientific limits

- Synthetic fixtures verify parser behavior, not agreement with a live
  Wannier90 version.
- The parser does not assess matrix unitarity or Hermiticity.
- It does not apply Hamiltonian degeneracies or interpolate bands.
- It supports only explicit WOUT `Ang` and `Bohr` labels and performs no unit
  conversion.
- It reports the ordered Wannierisation iteration inventory and last reported
  iteration, without making a convergence claim.
- Rectangular `_u_dis.mat` and selective-localization Omega variants are
  unsupported and rejected.
- Byte correlation establishes identity, not origin, correctness, or fitness.
