# Plane-wave DFT Wannierization scientific boundary

## Scope

The planned workflow capability represents the provider-neutral relationship
between a qualified plane-wave DFT parent and a candidate localized Wannier
representation. It records enough meaning to correlate state spaces and
operations without selecting a material, exchange-correlation approximation,
pseudopotential, structure, spin branch, reciprocal grid, projection family,
energy window, Wannier rank, tolerance, or scientific acceptance decision.

A consuming scientific project owns those choices and their justification. The
workflow may validate that declarations are complete and mutually consistent;
it does not choose values or promote evidence.

The parent structure and production numerical setting must arrive as one exact
accepted pair from the planned bulk qualification capability. Its first study
is scoped to the seed structure `S0`; zero-pressure relaxation produces a new
exact structure; final confirmation is scoped to that structure. If confirmation
changes the selected setting, re-relaxation and reconfirmation occur before this
Wannier route becomes eligible. This workflow consumes that lineage but does
not perform or authorize it.

The same rule applies to evidence profiles. A spectral Wannier campaign may
require only the complete eigenvalue/projection/overlap/localization route. A
represented component-operator campaign may additionally require authenticated
parent plane-wave coefficients or separately declared sampled-wavefunction
evidence. The scientific campaign declares that extension and any transformation
between representations. The neutral workflow must not equate UNK samples with
plane-wave coefficients, impose provider-native UNK output on every spectral
route, or silently omit a declared wavefunction-evidence role.

## Distinct state spaces

A route declaration must distinguish at least four spaces:

1. **Parent self-consistent state.** An exact accepted bulk
   structure/numerical-setting pair, electron model, pseudopotential set,
   reciprocal sampling declaration, coupled basis-cutoff policy,
   occupation rule, and solver policy produce a parent density, potential, and
   saved state.
2. **Uniform-grid Bloch frame.** One source-ordered reciprocal grid carries a
   declared band inventory, weights, spin convention, basis convention, and
   exact parent identity. A symmetry-reduced integration grid is not silently
   substituted for a declared full construction grid.
3. **Wannier construction subspace.** Projections, outer and optional frozen
   windows, retained bands, rank, neighbor topology, and gauge or
   disentanglement transformations define the construction being attempted.
4. **Localized real-space representation.** Lattice-vector-indexed Hamiltonian
   blocks, degeneracies, orbital order, centers, spreads, energy convention,
   and any truncation declaration describe the candidate representation.

A workflow handoff identifies which space it concerns. A direct Bloch object
and localized-basis object are not interchangeable merely because their array
shapes match.

## Separate scientific operations

The route keeps these operations distinct:

- predecessor bulk numerical and zero-pressure structural qualification;
- self-consistent parent construction;
- non-self-consistent evaluation on a declared reciprocal grid;
- preprocessing of localization topology and projection intent;
- provider-native interface generation;
- subspace selection or disentanglement;
- gauge selection and localization;
- basis transformation to a localized representation;
- real-space truncation, if any; and
- downstream interpolation, operator transformation, or comparison.

The predecessor operation is outside the later five calculator occurrences; it
supplies only an exact eligibility handoff. Completion of one operation does
not establish the correctness of another. In
particular, process success does not establish localization convergence;
localization convergence does not establish interpolation accuracy; and band
interpolation agreement does not establish that another represented operator
is accurate.

## Geometry and reciprocal conventions

Exact declarations must bind ordered direct-lattice vectors, row/column
convention, units, handedness, ordered atomic coordinates, and reciprocal-vector
convention, including the placement of any factor of `2 pi`. A basis change is
not represented as a filename change. If a route changes direct basis, its
consumer must retain the exact transform and corresponding reciprocal-coordinate
map.

The uniform grid is source ordered. Symmetry and time-reversal reduction policy
are explicit. Equivalent point sets in different orders can produce different
native index relationships and therefore require an explicit permutation
rather than implicit set equality.

## Band, subspace, and spin meaning

The parent band inventory, construction-band inventory, and Wannier rank are
separate quantities. An outer window may admit a varying band set over the
reciprocal grid; a frozen window may constrain an inner subspace; neither is
inferred from matrix dimensions alone. Degenerate or nearly degenerate states
require subspace-aware identity rather than an assumption that independently
sorted eigenvalue indices denote the same state.

Spin treatment is part of the model. Scalar non-spin-polarized, collinear spin,
noncollinear spin, and spin-orbit-coupled routes are not interchangeable.
Neutral handoffs carry a spin convention and component inventory without
encoding a provider keyword.

## Energy and gauge conventions

Every normalized observation states its energy reference. Scalar energy
alignment, state permutation, unitary transformation within a retained
subspace, disentanglement from an outer space, and real-space truncation are
separate operations. A downstream consumer must declare which transformations
are permitted before subtracting represented operators or comparing states.

Gauge-dependent matrices may be exact evidence for one construction without
being directly comparable to matrices from another construction. Gauge-invariant
spectra or projectors still require common momentum coordinates, state-space
identification, units, and parent-model compatibility.

## Evidence and acceptance limits

The workflow may report that exact identities, role cardinalities, source
ordering, dimensions, spin conventions, and parent lineage agree. Those are
mechanical and semantic consistency facts. It does not establish:

- numerical convergence beyond the exact predecessor policy and qualification
  evidence it consumes;
- adequacy or transferability of a pseudopotential or electronic model;
- appropriateness of projections, windows, or rank;
- localization convergence from return code alone;
- interpolation, velocity, curvature, effective-mass, or operator accuracy;
- a universal real-space truncation threshold;
- agreement with experiment; or
- scientific validation, evidence promotion, or publication acceptance.

A consumer may validly conclude that a route failed, was inconsistent, did not
localize, exceeded a prospective tolerance, or remained inconclusive. The
software must preserve those outcomes rather than coerce them into a successful
representation.

## Provider boundary

Quantum ESPRESSO and Wannier90 are possible outward implementations, not part of
the neutral scientific contract. QE-native saved-state layouts, QEXSD, and
`pw2wannier90.x` artifacts remain under the QE integration. Wannier90 native
input and output syntax and parsing remain under the Wannier90 integration.
The bulk qualification, parent, and Wannier contracts remain provider neutral.
Their first-party provider/native-to-neutral mappings belong in outward
`projectkoios.adapters`, while operational provider selection and invocation
belong to repository tools. The current Wannier90 integration is
execution-independent; future
preprocessing and localization execution require a separately reviewed outward
capability and do not exist merely because this route is documented.

## References

1. N. Marzari, A. A. Mostofi, J. R. Yates, I. Souza, and D. Vanderbilt,
   “Maximally localized Wannier functions: Theory and applications,” *Reviews
   of Modern Physics* **84**, 1419–1475 (2012),
   [doi:10.1103/RevModPhys.84.1419](https://doi.org/10.1103/RevModPhys.84.1419).
2. A. A. Mostofi *et al.*, “An updated version of wannier90: A tool for
   obtaining maximally-localised Wannier functions,” *Computer Physics
   Communications* **185**, 2309–2310 (2014),
   [doi:10.1016/j.cpc.2013.10.003](https://doi.org/10.1016/j.cpc.2013.10.003).
