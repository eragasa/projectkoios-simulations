# Quantum ESPRESSO band-path projection and QEXSD extraction

This component maps a cell-bound `PwDftBandsSimulation` to `pw.x` bands input
and maps the resulting full-precision QEXSD spectrum back to
`BandDiagramData`. `PwDftSimulation.unit_cell` is the only lattice source;
`QeBandsPathProjection` does not accept a bare path or another cell.
ProjectKoios renders the final diagram itself. The maintained pipeline does not
use `bands.x`, `plotband.x`, or GNU plotting files.

## Workflow boundary

The computational sequence is:

1. complete a compatible SCF calculation and retain its saved state;
2. run `pw.x` with `calculation = 'bands'` against that state;
3. supply the resulting parsed `data-file-schema.xml` as `QeQexsdData`;
4. validate the observed k-points against the declared path;
5. convert the schema-defined native spectral values into neutral diagram data;
6. pass that neutral data to an application-owned renderer.

Steps 1 and 2 require explicit calculator-execution authorization. The path
projection and extraction objects neither authorize execution nor discover
files.

## `QeBandsPathProjection`

The projection inspects the path's explicit coordinate-system enum.
`reciprocal-fractional` maps deterministically to `K_POINTS crystal_b`; the
native option is not an independently configurable string. Unsupported systems
are rejected. Every path vertex is written with an integer interpolation count.
For `points_per_segment = N`, every nonterminal vertex receives `N`; a branch's
terminal vertex receives `1`.

For a branch with `m` vertices, QE therefore emits

```text
(m - 1) * N + 1
```

samples. Unlike VASP line mode, a shared interior vertex is represented once.
The complete expected count is the sum over branches.

A branch boundary is encoded as a terminal vertex with count one followed by
the next branch's first vertex. This yields adjacent source rows but does not
declare an interpolated segment between them. `diagram_branches()` records the
separate half-open ranges needed by renderers.

### Example

For `L-Γ-X-U | K-Γ` and `N = 20`:

```text
branch 1: 3 * 20 + 1 = 61 samples
branch 2: 1 * 20 + 1 = 21 samples
total:                    82 samples
```

The projection preserves the caller's labels and coordinates. It does not
validate crystallographic symmetry or select a standard path. A caller may
first bind a calculator-neutral `SetyawanCurtaroloPathDefinition`; its validated
and, when necessary, basis-transformed path then follows this same projection
route without calculator-specific path logic.

## Authoritative source hierarchy

The maintained extraction hierarchy is:

1. parsed QEXSD `data-file-schema.xml` for full-precision structure, reciprocal
   lattice, k-points, eigenvalues, occupations, units, and source identity;
2. captured `pw.x` stdout for terminal state, warnings, and diagnostics;
3. optional postprocessor products only as separately identified derived
   evidence;
4. SVG/PNG as presentation products, never as numerical sources.

`bands.x` output is unnecessary when ProjectKoios owns the diagram and no
explicit symmetry/overlap-based band reordering has been requested. Its GNU
plot file is rounded and discards QEXSD metadata, so it is not consumed by
`QeBandsDataExtractor`.

## `QeBandsDataExtractor`

The extractor accepts an already constructed `QeQexsdData`; it does not parse
XML or open paths. The retained parsed document must expose the fields produced
by `QuantumEspressoXsdDocumentParser`, including:

- declared unit-system label and `alat`;
- reciprocal-lattice coefficients;
- source-ordered k-points;
- eigenvalues and optional occupations;
- declared sample and band counts;
- source identity retained by `QeQexsdData`.

Before interpreting k-points, the extractor reconstructs the QEXSD final
`UnitCell` and compares its source-ordered lattice vectors, atom symbols, and
fractional positions with `projection.calculation.simulation.unit_cell`.
A reordered or different basis is rejected even when symmetry would make the
resulting path physically equivalent. The default absolute cell comparison
tolerance is `1e-7`, allowing only bounded unit-conversion roundoff.

The extractor also fails closed when required fields are absent, the declared
unit system is unsupported, dimensions disagree, the expected band count
differs, or any observed k-point differs from the projected path beyond the
configured absolute tolerance.

### K-point validation

Let a declared fractional reciprocal point be

```text
q = (q1, q2, q3)
```

and let the three QEXSD reciprocal-lattice coefficient rows be `b1`, `b2`, and
`b3`. The expected native Cartesian coefficient is

```text
q_cart = q1*b1 + q2*b2 + q3*b3
```

Every observed QEXSD k-point is compared componentwise through its Euclidean
deviation from `q_cart`. The default maximum accepted deviation is `1e-10` in
that native coordinate representation. The largest observed deviation is
retained as `QeBandsData.maximum_kpoint_deviation`.

This check binds the spectrum to both the declared path and the exact reciprocal
basis. A matching sample count alone is insufficient.

### Reciprocal-distance coordinate

QEXSD k-points are retained in Cartesian coefficients scaled by `2π/alat`.
For adjacent points in one branch, the displayed increment in inverse angstroms
is

```text
Δs = ||q_cart(i) - q_cart(i-1)||
     * 2π / (alat_bohr * bohr_to_angstrom)
```

using:

```text
bohr_to_angstrom = 0.529177210903
```

Distances accumulate only within a declared branch. At a branch boundary, the
new branch starts at the preceding branch's final scalar coordinate; the
physical jump is intentionally not included.

### Energy and occupation handling

For the supported `Hartree atomic units` declaration, QEXSD eigenvalues are
converted as:

```text
E_eV = E_hartree * 27.211386245988
```

The conversion uses the CODATA 2018 Hartree-to-eV value. Occupations are
retained exactly as parsed; they are not rescaled or interpreted. The extractor
creates one neutral spin channel from one source row per projected k-point.
Spin-expanded layouts that do not have exactly one row per projected sample are
rejected rather than guessed.

An energy reference remains caller-supplied. The extractor does not infer the
Fermi energy, highest occupied level, valence-band maximum, or band gap.

## Failure modes

Extraction rejects, among other cases:

- QEXSD from an SCF mesh rather than the declared line path;
- a path expressed in a reciprocal basis different from the executed cell;
- omitted, duplicated, reordered, or extra samples;
- an unexpected number of bands;
- inconsistent eigenvalue or occupation row lengths;
- an unsupported unit-system label;
- nonpositive or nonfinite `alat`;
- a spin representation whose row layout is not currently modeled.

No fallback to stdout, `bands.x`, or a plot file occurs after such a failure.

## References

- [Quantum ESPRESSO 7.5 `pw.x` input description](https://www.quantum-espresso.org/Doc/INPUT_PW.html)
  documents `calculation='bands'` and `K_POINTS crystal_b`.
- [Quantum ESPRESSO QESchemas](https://gitlab.com/QEF/qeschemas) defines the
  structured XML vocabulary consumed by the maintained parser.

The repository retains an inert, identity-bound
[canonical QE 7.5 silicon software observation](../../../../../../../examples/projectkoios/integrations/quantumespresso/pw/bands/Si/primitive/reference-software-observation/README.md)
and the earlier
[superseded cyclic-basis observation](../../../../../../../examples/projectkoios/integrations/quantumespresso/pw/bands/Si/primitive/superseded-cyclic-basis-observation/README.md).
Their inputs and manifests do not grant reusable execution authority.

A successful extraction is a mechanical software observation. It does not
establish convergence, pseudopotential suitability, band connectivity,
physical accuracy, or scientific validation.
