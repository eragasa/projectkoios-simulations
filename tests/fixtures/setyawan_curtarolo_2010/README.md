# Setyawan–Curtarolo 2010 golden fixture

`appendix_a_golden.json` is a static regression fixture for the convention
published in Appendix A of:

> W. Setyawan and S. Curtarolo, *Computational Materials Science* **49**
> (2010) 299–312, DOI `10.1016/j.commatsci.2010.05.010`.

## Integrity

The SHA-256 digest of `appendix_a_golden.json` schema version 2 is
`2313d224a233767d6a19c756e6f6396021ca1c7462c932de9d509e240455ee59`.

## Attribution boundary

The standard-cell definitions, special-point formulas, and ordered path
topologies represented by the fixture are Setyawan–Curtarolo convention data.
The fixture identifies the corresponding Appendix-A table for every case.

The JSON organization, choice of finite numerical specimens, evaluation of the
published formulas at those specimens, test harness, immutable records,
validation logic, Cartesian-frame binding, and provider projections are
Project Koios work. No AFLOW source code is included or claimed as a source for
the implementation.

## Purpose and limits

The fixture freezes expected conventional and primitive lattice vectors, all
tabulated special points, and every ordered branch for the 25 Appendix-A
cases. It is maintained independently from the production package at test
runtime: tests read this static JSON and do not generate expected values through
production functions.

The fixture provides regression evidence for the transcription. It does not by
itself establish scientific validation, numerical convergence, calculator
conformance, symmetry inference, or automatic Bravais identification.
