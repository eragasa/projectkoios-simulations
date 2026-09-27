# Retained VASP negative-lattice-orientation failure

## Mathematical diagnosis

The generated POSCAR contained

$$
\begin{aligned}
\mathbf{h}_1 &= (2.715, 2.715, 0.000)\ \text{Å}, \\
\mathbf{h}_2 &= (2.715, 0.000, 2.715)\ \text{Å}, \\
\mathbf{h}_3 &= (0.000, 2.715, 2.715)\ \text{Å}.
\end{aligned}
$$

Its signed scalar triple product is

$$
\mathbf{h}_1 \cdot (\mathbf{h}_2 \times \mathbf{h}_3)
= -40.02575175\ \text{Å}^3,
$$

so the ordered basis is left-handed. Exchanging $\mathbf{h}_2$ and
$\mathbf{h}_3$ produces

$$
\det([\mathbf{h}_1\ \mathbf{h}_3\ \mathbf{h}_2])
= +40.02575175\ \text{Å}^3.
$$

To preserve Cartesian positions, every fractional position must receive the
matching transformation

$$
(s_1,s_2,s_3)^{\mathsf T}
\longmapsto
(s_1,s_3,s_2)^{\mathsf T}.
$$

Both silicon sites in this example are unchanged textually because their second
and third fractional components are equal.

## Native observation and workflow handling

This directory retains the bounded native observation from an authorized VASP
5.3.5 SCF attempt using the exact committed primitive-silicon inputs identified
by `manifest.json`.

VASP returned process status zero but did not perform the SCF calculation. Its
captured standard output states:

```text
ERROR: the triple product of the basis vectors is negative exchange two basis vectors
```

The maintained VASP SCF output analyzer maps this native observation to the
stable failure code `negative-lattice-orientation`. The calculator-neutral CPN
workflow carries that code to its terminal failure outcome. This behavior keeps
process completion distinct from calculator and workflow success.

The canonical silicon relaxation declaration performs the right-handed
transformation explicitly and preserves all basis-indexed quantities.
`PoscarWriter` does not silently reorder a basis. This retained output contains
a native VASP error, so the integration propagates it as the stable
`negative-lattice-orientation` failure. Application contracts and integrations
do not manufacture that error for calculators which accept the same ordering;
pre-execution rejection belongs to workflow policy or a future calculator
adapter. The explicit basis permutation is not structural relaxation.

`POTCAR` is identified by hash and size but is not copied into this repository.
No scientific result is claimed from this failed calculation.
