# `projectkoios.integrations.vasp.poscar`

The format authority is the official VASP [`POSCAR`](https://vasp.at/wiki/POSCAR)
documentation retained as `POSCAR_DOCUMENTATION_URL`.

## Mathematical representation

Let the physical lattice vectors be the columns of $H$:

$$
H = [\mathbf{h}_1\ \mathbf{h}_2\ \mathbf{h}_3].
$$

For a fractional column vector $\mathbf{s}$, its Cartesian position is

$$
\mathbf{r} = H\mathbf{s}.
$$

The signed cell volume is the scalar triple product

$$
V = \det(H)
  = \mathbf{h}_1 \cdot (\mathbf{h}_2 \times \mathbf{h}_3).
$$

The shared `Lattice3D.is_right_handed` property reports whether the ordered
basis has positive orientation:

$$
\texttt{is\_right\_handed} \iff \det(H) > 0.
$$

It reports orientation without changing basis-vector order or fractional
coordinates.

## POSCAR implementation

`UnitCellModel` binds the shared PhysKit unit cell to the POSCAR boundary.
`PoscarModel` adds the POSCAR comment and delegates serialization to
`PoscarWriter`.

The writer performs an order-preserving projection:

$$
H_{\mathrm{POSCAR}} = H,
\qquad
\mathbf{s}_{\mathrm{POSCAR}} = \mathbf{s},
$$

so

$$
H_{\mathrm{POSCAR}}\mathbf{s}_{\mathrm{POSCAR}} = H\mathbf{s}.
$$

It converts physical lengths to Å, emits a scale of `1.0`, writes the columns of
$H$ as lattice-vector lines, groups sites by first-occurring element symbol,
and writes the declared fractional coordinates under `Direct`. `render` is
deterministic and `write` is atomic. The writer does not select structures,
normalize orientation, or execute VASP.

A left-handed cell must not be corrected silently at this serialization
boundary. Any accepted orientation change must be represented explicitly and
must transform every basis-indexed quantity. For example, for a declared
permutation $P$,

$$
H' = HP,
\qquad
\mathbf{s}' = P^{\mathsf T}\mathbf{s},
$$

and the transformation is geometry-preserving only because

$$
H'\mathbf{s}' = HPP^{\mathsf T}\mathbf{s} = H\mathbf{s}.
$$

Ownership of such an explicit transformation or of a right-handedness
precondition remains outside `PoscarWriter` and must be decided before a new
VASP input declaration is accepted.

## Conformance status

The retained primitive-silicon failure demonstrates that the writer preserves
the declared left-handed order and that VASP rejects that input with the stable
workflow failure code `negative-lattice-orientation`. This is retained native
failure evidence, not authorization for the writer to mutate the basis.
