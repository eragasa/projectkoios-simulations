# Planned Wannier90 preprocessing scientific boundary

## Scientific meaning

Wannier90 preprocessing translates one exact localization-construction intent
into native neighbor-topology and projection-interface metadata. The future
integration may preserve and parse that meaning, but it does not select the
construction or determine whether it is scientifically suitable.

The consuming scientific owner supplies the exact lattice, reciprocal points,
spin treatment, number of Wannier functions, projections, excluded bands,
outer and optional frozen windows, and any provider controls. The provider
integration validates representability and consistency; it must not choose
fallback projections, widen windows, reduce a reciprocal grid, or change rank
to obtain a successful process.

## Native input meaning

The exact native input binds one seed to a construction. At minimum, the
scientific declaration distinguishes:

- ordered direct and reciprocal lattice conventions and units;
- ordered atomic coordinates and species semantics;
- source-ordered reciprocal points;
- spin branch and component selection;
- parent band inventory and explicitly excluded bands;
- Wannier rank and projection semantics;
- outer and optional frozen energy windows with energy units/reference;
- localization controls; and
- requested native output behavior.

A syntactically valid input is not evidence that these choices are physically
appropriate. The same material label or seedname does not make two
constructions equivalent.

## Neighbor topology

The preprocessing output describes reciprocal-point relationships and native
interface expectations. Its ordered neighbor inventory is part of the
construction identity. A future observation must preserve source and target
indices and reciprocal-lattice shifts rather than treating neighbors as an
unordered set.

A parseable topology does not establish that the grid is dense enough, that the
neighbor shell supports the intended interpolation, or that a later converter
will produce consistent overlaps. Those are downstream numerical and
scientific checks.

## Projection, window, and rank separation

Projection functions, parent bands, selected/disentangled subspaces, and
Wannier functions are different objects. Their counts need not all be equal.
The provider must preserve these distinctions and must not infer an unstated
selection map solely from equal dimensions.

Outer-window selection, frozen-window selection, disentanglement, gauge choice,
and localization are separate operations. Preprocessing records intent and
interface topology; it does not perform or validate the later subspace and
gauge operations.

## Energy, geometry, and spin

Energy-window values require a declared unit and energy reference. Geometry
requires ordered basis vectors, row/column convention, coordinate convention,
and any factor of `2 pi` in reciprocal vectors. Equivalent cells in different
bases require an explicit transform.

Non-spin-polarized, collinear spin-channel, noncollinear, and spinor routes are
not interchangeable. The provider observation carries the declared spin
semantics and rejects incompatible native values rather than silently mapping
between branches.

## Nonclaims

Preprocessing process completion and topology correlation do not establish:

- self-consistent-parent or NSCF numerical convergence;
- correctness or transferability of an electronic model;
- adequacy of projections, windows, rank, or reciprocal sampling;
- successful production of interface eigenvalues, projections, or overlaps;
- localization or disentanglement convergence;
- interpolation, effective-mass, or represented-operator accuracy;
- agreement with experiment; or
- scientific validation, evidence promotion, or publication acceptance.

The provider integration does not own acceptance thresholds. A consumer may
retain a completed preprocessing occurrence while rejecting or revising the
construction in a new declaration.

## References

1. N. Marzari, A. A. Mostofi, J. R. Yates, I. Souza, and D. Vanderbilt,
   “Maximally localized Wannier functions: Theory and applications,” *Reviews
   of Modern Physics* **84**, 1419–1475 (2012),
   [doi:10.1103/RevModPhys.84.1419](https://doi.org/10.1103/RevModPhys.84.1419).
2. A. A. Mostofi *et al.*, “An updated version of wannier90: A tool for
   obtaining maximally-localised Wannier functions,” *Computer Physics
   Communications* **185**, 2309–2310 (2014),
   [doi:10.1016/j.cpc.2013.10.003](https://doi.org/10.1016/j.cpc.2013.10.003).
