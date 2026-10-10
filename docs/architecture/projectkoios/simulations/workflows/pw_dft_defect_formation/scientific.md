# Plane-wave DFT defect-formation workflow scientific protocol

## Scientific questions

The initial Si:P and Si:B studies ask three separate questions:

1. What neutral substitution formation energy follows from compatible local
   defect, pristine, and elemental-reference calculations?
2. How much energy is released by internal ionic relaxation at a fixed host
   lattice?
3. How much additional energy is released when the periodic cell is also
   allowed to relax, and how do those quantities change with supercell size?

The workflow keeps these questions separate. One accepted result does not imply
acceptance of the others. The initial formation-energy studies are neutral:
`charge_state == 0` and `delta_n_electrons == 0`. Future charged calculations
must record nonzero `delta_n_electrons` with
`charge_state == -delta_n_electrons`, but charged formation-energy analysis
remains unavailable until its additional physical terms are represented.

Neutral Si:P is a spin-polarized doublet because its bound donor electron has
`S = 1/2` [4]. The ideal, ion-only, fully relaxed, and final-SCF specifications
therefore all declare the same doublet spin intent. This is separate from
`delta_n_electrons`, which remains zero for neutral Si:P. A non-spin-polarized
Si:P result is incompatible with this study rather than an interchangeable
lower-cost calculation.

## Matched defect series

Every 64-, 216-, and 512-atom host supercell produces matched Si:P and Si:B
records with identical scientific roles:

```text
host geometry -> ideal substitution -> ion-only relaxation -> full relaxation
                       |                       |                    |
                   final SCF               final SCF            final SCF
```

The ideal substitution preserves the exact host lattice and host positions.
The ion-only stage preserves that lattice and changes positions. The full stage
starts from the ion-only result and permits positions and cell parameters to
change under declared pressure controls.

This sequence provides clear provenance and comparable roles. It does not prove
that a relaxation reached the global minimum. Alternative initial distortions
or symmetry-breaking calculations may be required if evidence indicates
multiple local minima.

## Elemental references

The phase used for each elemental chemical potential is explicit. Diamond
silicon and the boron and phosphorus phases selected from separately declared
one-element pymatgen convex hulls receive local relaxation and final-SCF
calculations under a compatible energy model.

The Materials Project and pymatgen support phase discovery and phase-diagram
analysis [1, 2]. Their database energies are not mixed with local defect
energies. The selected structures become exact local inputs, and the subsequent
local evidence supplies `mu_Si`, `mu_B`, and `mu_P`.

## Strain-energy interpretation

The workflow uses the operational zero-pressure definition documented in the
[defect scientific basis](../../defects/scientific.md):

```text
E_strain = E_final_scf(ion-only) - E_final_scf(fully_relaxed).
```

This measures the energetic effect of releasing the fixed-cell constraint in
the finite periodic supercell. Elastic point-defect theory explains why cell
boundary conditions and interactions with periodic images matter [3]. The
workflow therefore reports the exact cell size and does not rename this value
as an isolated-defect elastic energy.

## Acceptance claims

A workflow policy may conclude only what it tests. Its terminal result must
state separately whether evidence supports:

- calculation completion;
- numerical compatibility;
- SCF convergence;
- ionic relaxation completion;
- cell relaxation completion;
- formation-energy size stability; and
- strain-energy size stability.

“Accepted” means the declared policy was satisfied for the retained evidence.
It does not mean experimental validation, universal transferability, or proof
that no lower-energy defect configuration exists.

## References

1. A. Jain *et al.*, “Commentary: The Materials Project: A materials genome
   approach to accelerating materials innovation,” *APL Materials* **1**,
   011002 (2013),
   [doi:10.1063/1.4812323](https://doi.org/10.1063/1.4812323).
2. S. P. Ong *et al.*, “Python Materials Genomics (pymatgen): A robust,
   open-source Python library for materials analysis,” *Computational Materials
   Science* **68**, 314–319 (2013),
   [doi:10.1016/j.commatsci.2012.10.028](https://doi.org/10.1016/j.commatsci.2012.10.028).
3. E. Clouet, C. Varvenne, and T. Jourdan, “Elastic modeling of point-defects
   and their interaction,” *Computational Materials Science* **147**, 49–63
   (2018),
   [doi:10.1016/j.commatsci.2018.01.053](https://doi.org/10.1016/j.commatsci.2018.01.053).
4. G. Tosi *et al.*, “Silicon quantum processor with robust long-distance
   qubit couplings,” *Nature Communications* **8**, 450 (2017),
   [doi:10.1038/s41467-017-00378-x](https://doi.org/10.1038/s41467-017-00378-x).
