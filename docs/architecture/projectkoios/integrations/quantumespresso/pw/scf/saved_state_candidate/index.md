# QE SCF saved-state candidate

`saved_state_candidate.py` defines the provider-owned, path-free candidate that
can accompany an unchanged successful `dft_pw_scf` terminal outcome.

The candidate binds the exact immutable child-export identity and Workflow
correlation identities, neutral simulation and prepared-input references,
rendered input, structure, `pw.x` executable, pseudopotentials, successful
execution and normalization evidence, an immutable saved-state artifact-set
identity, the strict saved-state manifest, and the existing child terminal
outcome and history head.

The record is provider evidence only. It does not establish Si-VC acceptance,
scientific adequacy, staging authority, calculator authority, or publication.

## Saved-state artifact-set derivation

[`QeScfSavedStateArtifactSetProjector`](../saved_state_artifact_set/) consumes
the canonical manifest bytes and ordered artifact-store references supplied by
an outer authorized retention boundary. It produces an immutable artifact-set
`DataObject`, a retention-independent logical identity derived from its exact
saved-state semantics, and the exact `QeScfCandidateSavedState` fragment used
here. Its separate canonical codec computes a payload digest over encoded bytes;
that digest is not the logical artifact-set identity. This provides one checked
projection path that derives the manifest digest, artifact count, byte total,
and artifact-set identity together. Direct candidate construction remains
possible and must satisfy the candidate's own invariants; the projection result
additionally validates exact source correlation. The source-verification
identity remains caller-supplied by the outer boundary and is bound, not
established, by this pure projection.

## Pure encoding boundary

`QeScfSavedStateCandidateJsonCodec`:

1. consumes immutable typed records;
2. produces exact canonical control-JSON bytes and owner encoding metadata;
3. performs no artifact retention, filesystem, network, clock, random,
   calculator, or authority operation; and
4. rejects noncanonical bytes, duplicate or unknown keys, invalid types,
   machine paths, and bounded-field violations.

An outer authorized artifact boundary may retain the returned bytes and must
separately establish any retained reference. No accepted versioned Workflow
artifact-envelope or payload-reference contract is currently consumed here.
Future Workflow integration must adapt through its reviewed public contract;
this provider module does not prescribe its fields, admission rules, or wire
format.

`QeScfSavedStateCandidateVerifier` checks the candidate against the exact
canonical saved-state manifest bytes, `CalculatorInputRecord`, path-free
`SimulationEvidenceRecord`, and existing `PwDftScfWorkflowSucceeded` outcome.
It verifies rendered-input, structure, executable, pseudopotential, manifest,
evaluation, task, completion, and convergence correlations. Artifact-store
resolution and source-byte verification remain isolated worker operations.

The codec requires `workflow.child_export_identity`, so changing or omitting the
linked immutable child export changes or invalidates the candidate identity.
The provider verifier does not resolve Workflow plans or terminal deliveries and
must not accept a caller-asserted export as proof. How an accepted Workflow
contract establishes and correlates that opaque owner-issued identity remains a
deferred cross-boundary concern.

## Deferred Workflow delivery

Historical design records proposed a post-terminal companion, an ordinal, and a
retention phase. Those proposals are non-current and non-authoritative: Workflow
has not accepted a public wire format, artifact envelope, companion-operation
contract, or compatibility promise for this candidate. They are therefore not a
conformance target for this module.

The canonical SNAKES-to-Workflow exporter, compiled plan/export identities,
golden parity fixture, accepted artifact-reference binding, and nested runtime
integration remain unavailable. Their identities must be derived by their
owners from future exact contracts; this module does not fabricate nominal
substitutes.
