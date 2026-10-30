# `pw2wannier90.artifacts` route-specific closure

## Status

The current implementation provides fail-closed converter artifact declarations
and native interface inspection through:

- `QePw2Wannier90ArtifactRole`;
- `QePw2Wannier90ArtifactDeclaration`;
- `QePw2Wannier90ArtifactObservation`; and
- `QePw2Wannier90ArtifactInspector`.

The implemented inspector requires exactly one seed-bound AMN, MMN, and EIG
artifact and checks their exact identities and bounded native dimensions. The
implemented converter configuration requires AMN/MMN output and rejects UNK and
SPN output as unsupported.

A separate existing `QeWannier90PlaneWaveArtifactManifest` models a more
specialized authenticated plane-wave route and currently requires one UNK per
reciprocal point. These two shapes are not a single closed end-to-end artifact
contract. The route-specific closure described below is planned architecture;
no new route-kind API, manifest revision, migration, or compatibility behavior
is implemented by this documentation.

## Closure decision

The authoritative target separates at least two route profiles:

1. **AMN/MMN localization route.** Required converter outputs are exact EIG,
   AMN, and MMN artifacts correlated with the NNKP preprocessing artifact and
   parent NSCF saved state. UNK is neither required nor silently expected.
2. **Explicit UNK-producing route.** UNK output is enabled only by a separately
   supported converter branch with a named consumer, exact per-point/spin
   inventory, storage policy, and additional dimensional checks. Its required
   UNK inventory does not change the AMN/MMN route.

SPN, `uHu`, `uIu`, and future native outputs are likewise route-qualified.
Adding a role to the role enum does not make it required, supported for
production, or scientifically meaningful in every route.

## Ownership boundary

This QE integration owns provider-native converter configuration, staging,
execution effects, streams, artifact names/formats, exact native inspection,
and adaptation to QE-provider observations. It does not own Wannier90
localization execution, neutral workflow roles, scientific window/projection
selection, route acceptance thresholds, scheduling, or execution authority.

Production integration modules must not import
`projectkoios.simulations.workflows`. The ProjectKoios simulations distribution must provide a separately reviewed
first-party outward `projectkoios.adapters` surface that maps authenticated QE
artifacts to neutral `pw_dft_wannierization` roles using public contracts from
both layers.

## Nonclaims

Exact output closure and dimension agreement establish provider artifact facts
only. They do not prove NSCF convergence, projection/window adequacy,
localization convergence, interpolation accuracy, or scientific validation.
This architecture does not claim that UNK production currently works.

See [`implementation.md`](implementation.md) for the future closure change,
[`schematics.md`](schematics.md) for route and adaptation flows,
[`scientific.md`](scientific.md) for artifact meaning,
[`numeric.md`](numeric.md) for exact route cardinality and dimension rules, and
the consolidated
[Tranche 1 review](../../../../../../pw-dft-wannierization-review.md) for the
reuse-first compatibility and migration decision.
