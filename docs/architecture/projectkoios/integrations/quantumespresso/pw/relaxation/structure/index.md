# `relaxation.structure`

For source-ordered QEXSD vectors and Cartesian atomic positions,

$$
H = [\mathbf a_1\ \mathbf a_2\ \mathbf a_3],
\qquad
\mathbf f_i = H^{-1}\mathbf r_i.
$$

The vectors and positions use bohr in the supported QEXSD semantic record.
This module extracts a PhysKit `UnitCell` from the immutable document produced
by `projectkoios.integrations.quantumespresso.qexsd.parsing.QuantumEspressoXsdDocumentParser`.
It does not parse XML, discover files, reorder lattice vectors, or wrap
fractional coordinates.

## Public symbols

- `QeQexsdFinalStructure`
- `QeQexsdFinalStructureExtractor`
