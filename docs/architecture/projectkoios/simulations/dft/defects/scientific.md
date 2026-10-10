# Plane-wave DFT defect binding scientific basis

## Scope

This document records scientific meaning specific to plane-wave DFT defect
calculations. The method-neutral formation and relaxation equations remain in
[`projectkoios.simulations.defects`](../../defects/scientific.md). Satisfying the
binding rules below does not establish that a functional, pseudopotential,
supercell, spin state, or correction model is scientifically adequate.

## Electronic charge

A plane-wave DFT specification records `delta_n_electrons`, the integer change
relative to the neutral electron count for the same nuclei and exact
pseudopotentials. Positive values mean electrons added. The structural defect
charge follows the opposite convention:

```text
q = charge_state = -delta_n_electrons.
```

A neutral substitutional species change can alter the neutral valence count
without changing `delta_n_electrons`. Replacing Si by P includes the phosphorus
valence electron in the neutral baseline. Neutral Si:P therefore has
`delta_n_electrons == 0`; removing the donor electron gives `q = +1` and
`delta_n_electrons == -1`.

Charged periodic DFT calculations generally require method- and boundary-
condition-specific treatment. Defect formation energies require electron
chemical potential, band-edge reference, electrostatic alignment, and
finite-size corrections, as reviewed by Freysoldt *et al.* [1]. The architecture
retains charged calculations but rejects incomplete charged formation-energy
arithmetic.

## Neutral donor and acceptor spin

Neutral substitutional phosphorus in silicon has a bound donor electron with
`S = 1/2` [2]. Replacing Si by B instead removes one valence electron from the
neutral baseline and leaves an odd-electron acceptor state. The current Si:P and
Si:B workflows therefore declare collinear spin-polarized doublets with an
absolute spin-channel electron difference of one. This spin intent is explicit
even though `delta_n_electrons == 0`.

The ideal, symmetry-broken, fixed-host-relaxed, and final-SCF specifications
used in one energy series must retain compatible spin intent. A non-spin-polarized
calculation is a different scientific specification, not an interchangeable
optimization. Evidence should retain observed total magnetization or
spin-channel populations when the calculator supplies them.

This requirement does not prove that semilocal DFT localizes a shallow donor
correctly. Donor binding, wavefunction extent, and spin density remain sensitive
to functional and finite supercell size.

## Energy compatibility

Subtracting two total energies requires more than matching units. The DFT
binding qualifies exchange-correlation treatment, exact pseudopotentials,
electronic charge, spin, occupations, cutoffs, sampling, calculator inputs, and
completion. Broad cross-code studies show why full settings and reproducibility
evidence matter when comparing solid-state DFT energies [3].

Different elemental reference cells need not use the same integer k-point mesh,
but they must follow an explicit convergence and compatibility policy. The
method-neutral package consumes the resulting qualification without embedding
these DFT-specific rules in its equations.

## References

1. C. Freysoldt, B. Grabowski, T. Hickel, J. Neugebauer, G. Kresse,
   A. Janotti, and C. G. Van de Walle, “First-principles calculations for point
   defects in solids,” *Reviews of Modern Physics* **86**, 253–305 (2014),
   [doi:10.1103/RevModPhys.86.253](https://doi.org/10.1103/RevModPhys.86.253).
2. G. Tosi *et al.*, “Silicon quantum processor with robust long-distance
   qubit couplings,” *Nature Communications* **8**, 450 (2017),
   [doi:10.1038/s41467-017-00378-x](https://doi.org/10.1038/s41467-017-00378-x).
3. K. Lejaeghere *et al.*, “Reproducibility in density functional theory
   calculations of solids,” *Science* **351**, aad3000 (2016),
   [doi:10.1126/science.aad3000](https://doi.org/10.1126/science.aad3000).
