# `PoscarWriter`

## Mathematical contract

For a physical column matrix

$$
H = [\mathbf{h}_1\ \mathbf{h}_2\ \mathbf{h}_3]
$$

and fractional position $\mathbf{s}$, `PoscarWriter` preserves both declared
orders:

$$
H_{\mathrm{POSCAR}} = H,
\qquad
\mathbf{s}_{\mathrm{POSCAR}} = \mathbf{s}.
$$

The Cartesian position therefore remains

$$
H_{\mathrm{POSCAR}}\mathbf{s}_{\mathrm{POSCAR}}
= H\mathbf{s}.
$$

The signed cell volume is

$$
V = \det(H)
  = \mathbf{h}_1 \cdot (\mathbf{h}_2 \times \mathbf{h}_3).
$$

PhysKit's shared `Lattice3D.is_right_handed` property reports whether $V>0$;
it does not reorder the basis.

## Implementation contract

`PoscarWriter.render` produces deterministic VASP 5 POSCAR text from a
`PoscarModel`. It converts lengths to Å, emits the columns of the unit-cell
matrix in their declared order, and emits each atom's declared fractional
coordinates under `Direct`.

The writer does not normalize handedness. A caller or integration policy may
reject a left-handed declaration, or a separate explicit transformation may
produce a new geometry-preserving declaration. The writer must not exchange
basis vectors or fractional-coordinate components implicitly.

`PoscarWriter.write` atomically writes the rendered text to an explicit `Path`,
rejects destination symlinks, and preserves an existing destination's
permission mode.

The retained silicon calculation demonstrates that a left-handed source cell
can produce the stable `negative-lattice-orientation` VASP workflow failure.
The ownership and representation of a future explicit correction remain to be
decided before regenerated input is committed.
