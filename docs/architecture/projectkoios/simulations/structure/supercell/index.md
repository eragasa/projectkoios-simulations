# Calculator-neutral supercells

`projectkoios.simulations.structure` represents an expanded periodic cell with
`SuperCell(UnitCell)`. A `SuperCell` retains:

- the exact source `UnitCell`;
- the three positive diagonal replication counts;
- the source atom index and integer source-cell translation for every output
  site.

For a source direct-lattice matrix whose vectors are columns, diagonal
replication by `n = (n1, n2, n3)` constructs

```text
A_super = A_source diag(n1, n2, n3)
```

and maps source fractional position `p` in translated image `t` to

```text
p_super = (p + t) / n.
```

`SuperCellBuilder.action()` accepts an immutable
`SuperCellConstructionRequest` and returns a correlated
`SuperCellConstructionResult`. Sites are ordered first by translations in
lexicographic `(i, j, k)` order and then by source atomic-basis order.
`UnitCellSiteOrigin` makes that ordering explicit rather than requiring callers
to infer it.

`SuperCellSubstitutor.action()` replaces exactly one site selected by its source
atom index and translation. Its result remains a `SuperCell`, preserves the
lattice, positions, replication declaration, and site provenance, and changes
only the selected chemical symbol. The action does not select a dopant, charge
state, spin state, relaxation policy, k-point mesh, or acceptable supercell
size. Those are separate simulation or application decisions.

For the eight-atom cubic conventional silicon cell, `(2, 2, 2)`, `(3, 3, 3)`,
and `(4, 4, 4)` replications contain 64, 216, and 512 atoms respectively.
