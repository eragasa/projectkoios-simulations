# Plane-wave DFT defect-formation workflow scientific protocol

## Scientific questions

The initial Si:P and Si:B studies ask three separate questions:

1. What neutral substitution formation energy follows from compatible local
   defect, pristine, and elemental-reference calculations?
2. How much energy is released by internal ionic relaxation at a fixed,
   locally optimized host lattice?
3. What residual stress remains under that dilute-defect boundary condition,
   and how do formation energy and stress change with supercell size?

The workflow keeps these questions separate. One accepted result does not imply
acceptance of the others. The initial formation-energy studies are neutral:
`charge_state == 0` and `delta_n_electrons == 0`. Future charged calculations
must record nonzero `delta_n_electrons` with
`charge_state == -delta_n_electrons`, but charged formation-energy analysis
remains unavailable until its additional physical terms are represented.

Neutral Si:P is a spin-polarized doublet because its bound donor electron has
`S = 1/2` [4]. Neutral substitutional Si:B likewise has an odd valence-electron
count: replacing four-valence-electron Si by three-valence-electron B leaves one
hole. Under the collinear single-determinant model, both defects therefore
require `abs(N_up - N_down) == 1`. Their ideal, ion-only, and final-SCF
specifications declare that constrained doublet intent. This is separate from
`delta_n_electrons`, which remains zero. An unpolarized neutral Si:P or Si:B
result is incompatible with this study rather than an interchangeable
lower-cost calculation.

## Matched defect series

The transferred conventional Si cell is a starting geometry, not the production
host lattice. A compatible local zero-pressure bulk relaxation first publishes
an observed conventional cell. Its 2×2×2, 3×3×3, and 4×4×4 replications then
produce matched 64-, 216-, and 512-atom pristine, Si:P, and Si:B records.

```text
local relaxed host -> pristine supercell -> ideal substitution
                                              |
                         symmetry-broken fixed-cell ion relaxation
                                              |
                                          final SCF
```

The primary dilute-defect protocol fixes every supercell to the same locally
optimized host lattice and relaxes atomic positions only. It does not use a
separately optimized cell for each finite defect concentration. Optional
full-cell calculations are finite-concentration strain diagnostics and cannot
replace the fixed-host formation-energy series.

Spatial symmetry and time-reversal k-point reduction are disabled for every
defect relaxation and its final SCF. Each size and species starts from the ideal
cell and from deterministic 0.01 angstrom impurity displacements along the host
`<100>` and `<111>` directions. All three occurrences retain distinct evidence;
the lowest compatible converged final-SCF energy is the reported observed
basin. A relaxation convergence flag alone is not called proof of a local or
global minimum. A stronger minimum claim requires separately specified
vibrational-stability evidence.

## Elemental references

The phase used for each elemental chemical potential is explicit. Diamond
silicon and the boron and phosphorus phases selected from separately declared
one-element pymatgen convex hulls receive local relaxation and final-SCF
calculations under a compatible energy model.

The Materials Project and pymatgen support phase discovery and phase-diagram
analysis [1, 2]. Their database energies are not mixed with local defect
energies. The selected structures become exact local inputs, and the subsequent
local evidence supplies `mu_Si`, `mu_B`, and `mu_P`.

## Strain interpretation

The primary series retains the final stress tensor from each fixed-host
relaxation and final SCF. Stress convergence with 64, 216, and 512 atoms is
reported independently from formation-energy convergence; stress is not folded
into the neutral formation-energy equation.

An optional zero-pressure full-cell diagnostic may evaluate the operational
quantity documented in the [defect scientific basis](../../defects/scientific.md):

```text
E_cell_release = E_final_scf(fixed-host) - E_final_scf(fully-relaxed).
```

This measures release of the fixed-cell constraint at one finite periodic defect
concentration. Elastic point-defect theory explains why boundary conditions and
periodic-image interactions matter [3]. The workflow reports exact cell size,
volume change, and boundary condition and does not rename this quantity as an
isolated-defect elastic energy.

## Acceptance claims

A workflow policy may conclude only what it tests. Its terminal result must
state separately whether evidence supports:

- calculation completion;
- numerical compatibility;
- SCF convergence;
- ionic relaxation completion;
- lowest-observed-basin selection across all declared starts;
- fixed-cell residual-stress size stability;
- optional cell-relaxation completion; and
- formation-energy size stability.

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
