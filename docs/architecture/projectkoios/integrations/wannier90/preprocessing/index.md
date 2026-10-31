# Planned Wannier90 preprocessing integration

## Status

A bounded render-only API now exists as
`projectkoios.integrations.wannier90.Wannier90PreprocessingInput`. It validates
the generic non-spin spectral subset, deterministically renders exact `.win`
bytes, separately prepares an authenticated calculator-input record, and
reports singular seed-derived `input_filename` and `nnkp_filename` values. The
`Wannier90PreprocessingNnkpOutput` value object binds exact observed `.nnkp`
bytes to their preprocessing declaration, derives the filename from its seed,
reports the observed byte size and SHA-256, and delegates bounded native
parsing. The separately available `prepare()` result is not redundantly stored
on this observation. Its
`verify_source_lattices_kpoints_and_excluded_bands()` method checks the ordered
direct lattice, derived reciprocal lattice including `2 pi`, reciprocal-
fractional k points, and excluded bands. The separately named
`verify_source_selected_projection_indices()` method bounds any selected source
indices against the expanded native projection inventory without reimplementing
Wannier90 projection expansion. Direct, reciprocal, and fractional coordinates
use separate Pint-backed PhysKit scalar tolerances supplied explicitly to the
verification call rather than stored as output state. The output
reports its observed filename, byte size, and SHA-256, but no separate retained
artifact identity exists before the execution-evidence persistence boundary is
implemented.

No production preprocessing runner, execution request or result type, complete
semantic input/output correlation, or verified topology handoff exists. The
current implementation does not invoke
`wannier90.x -pp`, grant execution authority, or establish calculator
compatibility or scientific acceptance.

## Purpose

The accepted first renderer scope is a reusable generic non-spin spectral
Wannier90 subset. Consuming projects supply every material-specific structure,
projection, window, mesh, rank, and control value. The future capability will
own Wannier90-native preparation and observation of one preprocessing
occurrence. Its bounded responsibility is to:

1. consume an exact caller-selected construction declaration or exact
   authenticated `.win` bytes;
2. project or stage one deterministic seed-bound native input;
3. verify the exact `wannier90.x` executable and declared resources before side
   effects;
4. submit at most one separately authorized `wannier90.x -pp <seedname>`
   process through the generic single-attempt executor;
5. retain native stdout, stderr, terminal execution evidence, and exact output
   identities; and
6. parse and normalize the resulting neighbor-topology observation without
   applying scientific acceptance policy.

Configuration and exact input identity do not authorize execution. Rendering or
inspection must remain available without an executable, output process, or
execution resources.

## Ownership boundary

This outward integration owns native Wannier90 syntax, seedname rules,
preprocessing command projection, provider-specific input and output manifests,
and adaptation of authenticated native topology into provider observations. It
does not own:

- material, structure, pseudopotential, spin, projection, window, rank, mesh, or
  tolerance selection;
- the provider-neutral `pw_dft_wannierization` route;
- Quantum ESPRESSO saved-state or `pw2wannier90.x` behavior;
- occurrence scheduling, retries, leases, cancellation, or durable runtime
  state;
- reusable execution authority or executable discovery; or
- scientific acceptance of the construction or resulting topology.

The future production module may depend on protected
`projectkoios.simulations` execution and artifact contracts. It must not import
`projectkoios.simulations.workflows`. A first-party outward `projectkoios.adapters` surface must import both public
sides and map this provider observation to neutral roles without reversing
either production dependency.

## Required handoff

A successful provider handoff will identify, at minimum:

- exact input bytes and their construction source;
- seedname and native input basename;
- exact executable and terminal execution-record identities;
- exact stdout and stderr artifacts;
- exact neighbor-topology artifact identity;
- observed lattice, reciprocal points, neighbor inventory, projections, and
  excluded-band declarations supported by the parser; and
- enough predecessor identity to correlate the output with the caller's
  construction declaration.

The handoff is non-authorizing and immutable. A matching seedname or basename is
not sufficient identity. Missing output, changed bytes, native parse failure,
source-order disagreement, or inconsistent dimensions produces retained
failure evidence rather than a successful handoff.

## Nonclaims

A zero return code and a parseable topology do not establish that projections,
energy windows, rank, or reciprocal sampling are scientifically appropriate.
Preprocessing does not localize orbitals, generate the QE interface artifacts,
prove that a later localization will converge, or accept a Wannier
representation.

See [`implementation.md`](implementation.md) for the current rendering seam and
remaining implementation boundary, [`schematics.md`](schematics.md) for
authority and adaptation flows, [`scientific.md`](scientific.md) for native
semantic limits, and
[`numeric.md`](numeric.md) for exact identity, ordering, and dimension rules.
