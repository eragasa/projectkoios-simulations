# Donor import closure

This inventory was resolved statically at donor commit
`7bd913151f7e61ed2bdba593df920be36573b502`; no donor code was executed.

## Extracted closure

The seven parser files are the complete implementation subtree
`1b5c6cd4a46f2fe70859c3aa1fded938a497e4dc`. Individual source paths and blobs
are recorded by `[[extractions.file_mappings]]` in `TRANSFER.toml`. The complete
donor test path is
`python/tests/software_verification/ksdft2effmass/integration/wannier90`, tree
`e5093059c62650e2afe14dccd80f25544e05c1df`; all 15 test modules and three
resources were transferred, then namespace/import/resource paths were rewritten
and failure coverage was added.

The common donor and destination Apache-2.0 license has SHA-256
`c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`.

## Direct semantic dependency

Every quantity import through `ksdft2effmass.operators` resolves semantically to:

| Path | Blob | Ownership |
| --- | --- | --- |
| `python/src/ksdft2effmass/operators/quantities.py` | `d98be473e19e17a59563fc7c3e00cca02fd822d3` | Generic physics infrastructure; PhysKit |

The donor test directly covering the used complex matrix wrapper is
`python/tests/software_verification/ksdft2effmass/operators/test__ComplexMatrixQuantity.py`,
blob `2e81f0cc1189a7d818c17c25637be408ec286d1e`. The complete operator test tree is
`6c01d90651f6d389c86882a2c6d9f61d723b7ab8`.

The pinned PhysKit replacement is `src/physkit/units/quantities.py`, blob
`686d075852ed01aab0a8d74fdec1be5a440c075d`, within units tree
`3314b0954e1d8e281e43f8f286e3e7c25361503d` at commit
`97032f16c9125aa124750508f8513cca9f6dab02`. Its used unit and quantity behavior
matches the donor module; PhysKit additionally provides nominal base classes.
Its MIT license has SHA-256
`0c4bfe022416818496cdcd7cf6fcd39af30c12a8e982cfb92d7a565d57dcc410`.

## Incidental package-facade closure not extracted

The donor imported from the broad `ksdft2effmass.operators` package facade.
Importing that facade would incidentally load operator tree
`adfbe02b04b5b2b066213ac9266a704bed16d517`:

```text
756ee89851c1e01641ed71e8840d32783dcf5b5d  operators/__init__.py
13fa6073cd3c8bcd977b8ce613dfdb270990329d  operators/comparison.py
363fe9f44a63a788b302c96225fef62a43142ded  operators/compatibility.py
ec79c26f4f3e4770c3bb25859f389d3e9bcfce8d  operators/complex_eigenpairs.py
428edeeec6d4fa330d374bec892d702aac08f9c3  operators/complex_eigensolvers.py
0fe4dc33f36313c9b6c6dc5d3bff901612954bb3  operators/difference.py
2c635512490df68c850f808dab45eeaa9cbcb9a5  operators/eigenpairs.py
afe519a1947da52e84631f9084985dff46b59348  operators/finite_differences.py
166ca0176698d541c00f6c45637ee360bf84f959  operators/hermiticity.py
a5c27dc22b0e84e7a2b25af6a69f5b64ccf57a36  operators/ladder_operators.py
dee104bb95d2ba1f8c4eb4c10b2c4f7553bce432  operators/matrix_norms.py
d98be473e19e17a59563fc7c3e00cca02fd822d3  operators/quantities.py
937cb90f09fe667a62b0261e2950c2fd0672892b  operators/records.py
3be84cec07944a41a928f9de1c13cb1c593817d1  operators/residuals.py
a095a5e072f0de7938a089ba567ce7945997c081  operators/serialization.py
1ee1fc37d1e169fc884277ad87574b81d7c27a15  operators/sparse_hermiticity.py
cf2c8bbe0e948aa27fa4ecb3a8bad37dbd1aa097  operators/subspaces.py
```

The facade's serialization adapter would also load serialization tree
`78d588e548ca36c02350e133728cfce700c0279c`:

```text
09c3680515d99c7224882a4465578dc62c561e7c  serialization/__init__.py
3dfec5b6bde53b588650868f70c76f431e582291  serialization/contracts.py
```

Those incidental operators, solvers, Hamiltonians, workflows, and serializers
are not parser requirements and were not extracted. External dependencies of
the generic donor quantity module were NumPy, Pint, and SciPy; they remain
owned through PhysKit, while NumPy is also declared directly because parser
modules import it.
