# Calculator-neutral band paths and diagram data

This module defines the calculator-neutral records shared by provider extraction
and application presentation. It also provides an explicitly declared
Setyawan--Curtarolo 2010 standard-cell and band-path catalog. It deliberately
does **not** define a calculator runner, XML parser, crystal-symmetry inference,
band-gap analyzer, plotting policy, or scientific acceptance rule.

`PwDftSimulation.unit_cell` is the sole lattice source. A
`PwDftBandsSimulation` composes that base simulation with a `BandPath` and
requires `calculation_type = bands`. Providers receive the composed record;
they may not accept an unbound path with an independent lattice.

## Data flow

```text
cell-specific declared path
        |
        +--> provider input projection --> calculator execution
                                             |
                                             v
                                  native structured output
                                  (QEXSD or vasprun.xml)
                                             |
                                             v
                                   provider data extractor
                                             |
                                             v
                                      BandDiagramData
                                             |
                                             v
                              application-owned presentation
```

A regular SCF/NSCF sampling mesh is not a band path. Band-path data is accepted
only when an ordered path was declared and the provider-observed k-points are
mechanically checked against that declaration.

## Path records

`BandPathVertex` retains:

- a nonempty, stripped display label;
- exactly three finite fractional reciprocal coordinates.

The coordinates are coefficients of the reciprocal vectors of the **specific
simulation cell**. A coordinate triple is therefore not meaningful without the
cell and basis ordering used by the calculation.

`BandPathBranch` contains at least two source-ordered vertices and represents
one continuous polyline in reciprocal space. `BandPath` contains one or more
branches, an explicit `BandPathCoordinateSystem`, and a nonempty
convention/source description. The currently supported coordinate system is
`reciprocal-fractional`. Multiple branches are used for intentional
discontinuities. For example, `L-Γ-X-U | K-Γ` consists of two branches; no
`U-K` segment exists.

Generic paths remain caller-declared. If the unit-cell basis is reordered, the
fractional reciprocal coordinates must be transformed or the old binding must
be rejected.

## Setyawan--Curtarolo 2010 catalog

`projectkoios.simulations.dft.pw.setyawan_curtarolo_2010` contains
`SetyawanCurtaroloLattice` and `SetyawanCurtaroloPathDefinition`. The year is
part of the package name so a later convention revision cannot silently replace
the 2010 contract. The records implement the standard primitive cells,
special-point coordinates, parameter formulas, and path topologies in Appendix
A of:

> W. Setyawan and S. Curtarolo, *Computational Materials Science* **49**
> (2010) 299--312, DOI
> [`10.1016/j.commatsci.2010.05.010`](https://doi.org/10.1016/j.commatsci.2010.05.010).

The catalog covers CUB, FCC, BCC, TET, BCT1--2, ORC, ORCF1--3, ORCI, ORCC,
HEX, RHL1--2, MCL, MCLC1--5, and TRI1a/1b/2a/2b. Metric-dependent coordinates
are evaluated from the declared conventional lengths and angles. The
`standard_special_points` property exposes the complete tabulated point set;
`path` retains the paper's ordered branch topology. The record rejects
declarations that violate the paper's ordering or Appendix-A case conditions.

The year-scoped package separates responsibilities without fragmenting each
lattice into its own module:

- `model.py` owns the citation identity, Bravais names, and Appendix-A case
  labels;
- `selection.py` owns the case-selection request `DataObject`, correlated
  result, and `DataObjectActionizer`;
- `lattice.py` owns the declared lattice-case `DataObject`, standard cells, and
  metric-case validation, reusing
  `DirectLattice3D.from_lattice_parameters()` for the general canonical
  triclinic embedding while retaining source-specific Appendix-A basis order
  and orientation elsewhere; this also applies DirectLattice3D's dimensionless
  `1e-8` directional-independence policy to that embedding;
- `appendix_a.py` owns the cited special-point formulas and path tables;
- `binding.py` owns the path-definition and binding-request `DataObject`s,
  correlated result, binding `DataObjectActionizer`, and reciprocal-coordinate
  transformation;
- `_linear_algebra.py` owns private row-matrix operations.

The mathematical definitions represented by the golden fixture are attributed
to Setyawan and Curtarolo. The Python architecture, validation, formula
evaluation, test harness, and provider projection are Project Koios work; no
AFLOW source code is included.

The Bravais identity is explicit and caller-declared: the caller supplies one
of the 14 `SetyawanCurtaroloBravaisLattice` values. A
`SetyawanCurtaroloAppendixACaseSelectionRequest` retains the complete declared
metrics, and `SetyawanCurtaroloAppendixACaseSelector.action()` returns a
`SetyawanCurtaroloAppendixACaseSelectionResult` that correlates that request
with the uniquely selected metric-dependent Appendix-A case, including BCT,
ORCF, RHL, MCLC, and TRI boundary cases. Advanced callers may construct an
explicitly declared `SetyawanCurtaroloAppendixACase`, which is checked against
the same conditions.
The implementation does not infer a space group, primitive reduction, centering,
or Bravais lattice from atomic coordinates. This prevents metric coincidence
from being mistaken for a symmetry determination.

A `SetyawanCurtaroloPathBindingRequest` retains the path definition, exact
simulation, optional declared direct-basis transform, and dimensional tolerance.
`SetyawanCurtaroloPathBinder.action()` returns a
`SetyawanCurtaroloPathBindingResult` that retains the request, provider-ready
calculation, and whether its exact basis transform was declared or recovered.
The action compares the simulation lattice with the paper's standard primitive
lattice. With lattice vectors represented as rows,
it accepts

```text
A = U S R
```

where `S` is the paper-standard basis, `U` is an integer-unimodular direct-basis
change, and `R` is a proper Cartesian rotation. It validates this relation from
rotation-invariant lengths and determinant orientation. Reciprocal-fractional
path rows transform as `q_A = q_S U^T`; the Cartesian rotation does not change
the fractional coefficients.

The binder recovers `U` automatically when the bases share a Cartesian frame
and recognizes a pure rotation as `U = I`. A nonidentity basis change combined
with an arbitrary rotation must declare `direct_basis_transform` explicitly,
avoiding an ambiguous unbounded search through integer basis matrices. A
distorted or unrelated cell is rejected. The convention overview is documented
in `setyawan_curtarolo_2010/__init__.py`; the local derivation and tolerance
semantics remain beside the implementation in `binding.py` and
`_linear_algebra.py`. Providers still read lattice geometry only from
`PwDftSimulation.unit_cell`. The resulting `BandPath` retains a
`BandPathConventionProvenance` DataObject with the convention name, exact
`2010 Appendix A` revision, DOI, Bravais identity, Appendix-A case, and integer
direct-basis transform. Its human-readable `convention` remains presentation
metadata rather than the only provenance source.

The paper defines path topology, not a universal number of interpolated samples.
QE and VASP projection retain their explicit provider-level sampling controls.
A typical binding is:

```python
selection_request = SetyawanCurtaroloAppendixACaseSelectionRequest(
    bravais_lattice=SetyawanCurtaroloBravaisLattice.cubic_face_centered,
    a_angstrom=5.43,
    b_angstrom=5.43,
    c_angstrom=5.43,
)
selection = SetyawanCurtaroloAppendixACaseSelector().action(
    request=selection_request,
)
definition = SetyawanCurtaroloPathDefinition(selection.lattice)
binding = SetyawanCurtaroloPathBinder().action(
    request=SetyawanCurtaroloPathBindingRequest(
        definition=definition,
        simulation=bands_simulation,
    )
)
calculation = binding.calculation
```

Here `bands_simulation` is a `PwDftSimulation` whose calculation type is
`bands`; `binding.calculation` is the provider-ready `PwDftBandsSimulation`.
Both results retain their complete requests.

The maintained neutral silicon declaration is under
`examples/projectkoios/simulations/dft/pw/Si/primitive/`. Its VASP-Wiki and
Setyawan--Curtarolo declarations independently bind to the SHA-256 identity of
the canonical `Si.primitive.json` basis.

## Diagram records

`BandDiagramBranch` maps one declared path branch onto a half-open sample range
`[start_index, stop_index)`. Its tick indices are strictly increasing and its
tick labels must exactly match the corresponding `BandPathBranch` vertex
labels.

`BandDiagramData` retains:

- the complete `PwDftBandsSimulation`, including its exact `UnitCell`;
- the declared `BandPath` through that calculation;
- optional sampled fractional reciprocal k-points;
- a finite, nondecreasing path-coordinate array;
- an explicit label describing that coordinate;
- branch ranges and tick indices;
- energies in the fixed shape `[spin][sample][band]`, in eV;
- optional occupations with exactly the same shape;
- an optional energy reference and its required descriptive label.

All spin channels must have identical sample and band dimensions. Every branch
range must be in bounds and branches must cover samples in source order without
overlap. The data object rejects malformed or ambiguous shapes rather than
repairing them.

At a discontinuity, the first sample of the new branch uses the same scalar plot
coordinate as the final sample of the previous branch. Renderers must draw the
branches separately. This keeps the x-axis compact without manufacturing a
line between physically disconnected k-points.

## Energy references

Raw `energies_ev` are retained unchanged. `shifted_energies_ev` subtracts
`reference_energy_ev` only when the caller supplied both:

```text
E_display(n,k,s) = E_native(n,k,s) - E_reference
```

No implicit reference is selected. In particular, the neutral model does not
infer or equate:

- Fermi energy;
- highest occupied level;
- valence-band maximum;
- vacuum level;
- a reference from another calculator.

Those choices have different meanings, especially for metals, charged cells,
spin-polarized systems, and cross-provider comparisons.

## What this model does not establish

Mechanical path agreement and well-formed spectra do not establish:

- SCF convergence;
- cutoff, k-mesh, or band-count convergence;
- pseudopotential equivalence;
- band connectivity through crossings;
- a direct or indirect gap;
- agreement with experiment;
- scientific validation.

Any band-gap analysis or cross-provider alignment must be a separately declared
application policy operating on these retained observations.
