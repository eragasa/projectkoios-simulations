# VASP line-mode projection and `vasprun.xml` band extraction

This component renders a cell-bound `PwDftBandsSimulation` as VASP line-mode
`KPOINTS` and correlates the resulting structured `vasprun.xml` data with that
exact simulation and path. `PwDftSimulation.unit_cell` is the only lattice
source. It does not use plotting programs or parse values back from an image.

## Workflow boundary

A conventional semilocal VASP workflow is:

1. run a compatible SCF calculation on a regular mesh;
2. retain its converged `CHGCAR` with source identity;
3. run a non-self-consistent line-mode calculation, normally with `ICHARG=11`;
4. parse `vasprun.xml` and the other independently retained VASP sources;
5. extract neutral `BandDiagramData`;
6. render it in the application package.

VASP documents that a line-mode path is unsuitable for constructing the charge
density and recommends freezing a converged density with `ICHARG=11`. Execution
continues to require explicit authorization; neither the KPOINTS writer nor the
data extractor grants it.

## `VaspLineModeKpoints`

The record writes:

```text
<comment>
<points per segment>
Line-mode
Reciprocal
<segment start> ! <label>
<segment stop>  ! <label>

...
```

The writer inspects the path's explicit coordinate-system enum.
`reciprocal-fractional` maps deterministically to VASP `Reciprocal`; the native
label is not independently configurable. Coordinates are coefficients of the
exact simulation cell's reciprocal vectors. Each consecutive pair is one
segment. Blank lines preserve segment boundaries for human inspection.

VASP line mode includes both endpoints for every segment. With `N` points per
segment, each segment therefore contributes exactly `N` XML k-point rows. A
vertex shared by consecutive segments occurs twice. For example, a three-segment
continuous branch contributes `3*N` rows, not `3*N+1`.

Separate `BandPathBranch` records remain separate segment groups. The writer
does not create a segment across a declared discontinuity. A calculator-neutral
`SetyawanCurtaroloPathDefinition` can be bound before projection; the VASP
writer consumes its validated, basis-transformed `PwDftBandsSimulation` without
owning a second path catalog.

## `VaspBandDataExtractor`

The extractor requires `VaspDataSources` containing parsed `vasprun.xml` data
and the same `PwDftBandsSimulation` used for projection. Before interpreting the
path, it compares the source-ordered initial XML lattice vectors, atom symbols,
and fractional positions with `calculation.simulation.unit_cell`. A reordered
or different basis is rejected even when crystal symmetry would make it
physically equivalent. It also rejects missing spectra or occupations and
validates the declared number of bands.

It independently reconstructs every expected line-mode sample from the declared
path and `points_per_segment`:

```text
q_j = q_start + j/(N-1) * (q_stop - q_start),  j = 0..N-1
```

The source-ordered `vasprun.xml` k-points must have the exact expected count and
must match within the configured absolute coordinate tolerance (`1e-7` by
default). A matching count without matching coordinates is rejected.

The extracted `VaspBandConsistency` reports mechanical agreement between
independent native sources for:

- VASP program version;
- atom count;
- k-point count;
- the configured simulation unit cell;
- declared path coordinates.

These observations do not merge the sources and do not constitute scientific
acceptance.

## Reciprocal-distance coordinate

Let `A` contain the three direct lattice vectors from the initial
`vasprun.xml` structure as rows, in angstroms. The reciprocal row matrix is

```text
B = 2π * inverse(A)^T
```

For two adjacent fractional reciprocal points, the path increment is

```text
Δs = ||(q_i - q_(i-1)) * B||
```

in inverse angstroms. Distances accumulate within each declared branch only.
The scalar coordinate is continuous at a branch boundary, but the renderer must
draw separate polylines so no physical segment is implied.

Eigenvalues are retained in the eV units supplied by `vasprun.xml`.
Occupations are retained without reinterpretation. Energy-reference selection is
explicit caller policy; the extractor does not automatically select `efermi`, a
highest occupied state, or a valence-band maximum.

## Source and cell requirements

Fractional reciprocal labels are basis-dependent. The declared path must be
valid for the exact POSCAR lattice-vector ordering used by the run. Primitive
and conventional cells generally use different reciprocal coordinates even
when they represent the same crystal.

The VASP fcc-silicon example declares `L-Γ-X-U | K-Γ`. The vertical bar is a
branch discontinuity, not a `U-K` segment. A rendered combined label such as
`U | K` at one scalar x-position communicates this discontinuity.

## Failure modes

Extraction fails rather than guessing when:

- `vasprun.xml` is absent;
- eigenvalues or occupations are absent;
- the spin/sample/band shape is inconsistent;
- the band count differs from the declaration;
- the XML k-point count differs from line-mode semantics;
- any XML k-point disagrees with the declared path;
- the declared path belongs to a different reciprocal basis.

## References

- [VASP KPOINTS documentation](https://vasp.at/wiki/KPOINTS) defines reciprocal
  coordinates, line-mode endpoint inclusion, and the frozen-density workflow.
- [VASP fcc Si bandstructure example](https://vasp.at/wiki/Fcc_Si_bandstructure)
  gives the `L-Γ-X-U | K-Γ` path and requires a converged `CHGCAR` with
  `ICHARG=11`.

The repository retains an inert, identity-bound
[canonical VASP 5.3.5 silicon software observation](../../../../../../examples/projectkoios/integrations/vasp/bands/Si/primitive/reference-software-observation/README.md)
and the earlier
[superseded cyclic-basis observation](../../../../../../examples/projectkoios/integrations/vasp/bands/Si/primitive/superseded-cyclic-basis-observation/README.md).
Their inputs and manifests do not grant reusable execution authority.

Successful extraction verifies software integration and source consistency. It
does not establish cutoff convergence, k-mesh convergence, pseudopotential
quality, physical accuracy, or scientific validation.
