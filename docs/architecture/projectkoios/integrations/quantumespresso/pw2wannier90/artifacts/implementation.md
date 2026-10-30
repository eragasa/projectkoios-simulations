# `pw2wannier90` artifact implementation rules

## Reuse-first decision

The current ordinary converter path already stages and executes
`pw2wannier90.x`, requires AMN/MMN output, and inspects exact EIG/AMN/MMN
artifacts. The first complete Wannier route reuses that path unchanged.

The separate existing `QeWannier90PlaneWaveArtifactManifest` remains a
specialized UNK/downstream-artifact aggregate. It is not widened, migrated,
deprecated, or used as the ordinary converter observation.

## Ordinary localization closure

At the first-party adapter/route-correlation boundary, one existing
`QePw2Wannier90ArtifactObservation` must close exactly:

- one seed-bound EIG;
- one seed-bound AMN; and
- one seed-bound MMN.

The correlation also binds the exact converter execution, parent NSCF saved
state/QEXSD, NNKP preprocessing artifact, prefix, seed, spin convention, and
existing parsed dimensions. UNK is absent. Downstream `.wout`, gauge,
disentanglement, and Hamiltonian files are localization outputs, not converter
outputs.

The current inspector may observe enum-recognized extras. The ordinary route's
closed retained-evidence profile rejects undeclared selected roles at the
adapter/correlation boundary without changing the inspector API. This does not
require rejection of every incidental file in the converter's private work
directory; incidental files are ignored or separately inventoried and never
silently promoted to route evidence.

## Specialized aggregate compatibility

Keep these current public surfaces and tests unchanged:

- `QeWannier90PlaneWaveArtifactManifest`;
- `QeWannier90PlaneWaveManifestVerifier`; and
- `QeWannier90ProviderCorrelationValidator`.

Do not make their UNK inventory optional or append AMN/MMN fields to schema one.
There is no lossless migration to ordinary converter closure because the
specialized aggregate lacks AMN/MMN and spans multiple producer stages.

UNK, SPN, `uHu`, `uIu`, and component-operator production remain separate
future route work. Enum membership alone does not establish production support.

## Provider-to-neutral adaptation

QE production modules remain unaware of neutral workflow types. First-party
`projectkoios.adapters` consumes existing QE observations and generic execution
and artifact identities to map the closed EIG/AMN/MMN set to neutral route
roles. The mapping retains exact source/target identities and decides no
scientific acceptance.

## Verification requirements

Calculator-free tests must prove:

- exact EIG/AMN/MMN singleton closure;
- parent, NNKP, execution, prefix, and seed agreement;
- dimension and source-order agreement using existing parsers;
- rejection of missing, duplicate, altered, unsafe, or undeclared selected
  retained-evidence artifacts;
- no UNK requirement in the ordinary route;
- unchanged current converter and specialized-manifest APIs/tests; and
- no workflow imports in QE integration modules.

These checks establish provider software consistency only, not localization or
scientific validity.
