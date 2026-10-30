# Planned Wannier90 preprocessing integration

## Status

This node specifies a planned outward provider capability. No production
preprocessing package, public request or result type, projector, runner, or
execution API described here exists. The current
`projectkoios.integrations.wannier90` implementation remains an
execution-independent parser of caller-supplied native artifacts. This
documentation does not change that status and grants no calculator execution
authority.

Implementation requires a separate reviewed change. Until that change exists,
consumers must not cite this node as evidence that ProjectKoios can render a
Wannier90 input, invoke `wannier90.x -pp`, or produce a verified preprocessing
handoff.

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

See [`implementation.md`](implementation.md) for the future implementation
boundary, [`schematics.md`](schematics.md) for authority and adaptation flows,
[`scientific.md`](scientific.md) for native semantic limits, and
[`numeric.md`](numeric.md) for exact identity, ordering, and dimension rules.
