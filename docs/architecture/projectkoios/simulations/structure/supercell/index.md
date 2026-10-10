# Calculator-neutral supercells

`projectkoios.simulations.structure` represents an expanded periodic cell with
`SuperCell(UnitCell)`. A `SuperCell` retains:

- the exact source `UnitCell`;
- three positive diagonal replication counts;
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
`UnitCellSiteOrigin` records that ordering explicitly.

The builder accepts only positive diagonal repetitions. A future general
supercell contract should use an integer transformation matrix rather than
silently overloading these three repetition counts.

Defects do not mutate a `SuperCell` or preserve a claim that the result is
pristine. Vacancies, interstitials, substitutions, and complexes are declared
with [`UnitCellDefectDelta`](../defect/index.md), whose application returns a
base `UnitCell`.

For the eight-atom cubic conventional silicon cell, `(2, 2, 2)`, `(3, 3, 3)`,
and `(4, 4, 4)` replications contain 64, 216, and 512 atoms respectively. Cell
construction does not choose a scientifically appropriate size and does not
authorize calculator execution.
