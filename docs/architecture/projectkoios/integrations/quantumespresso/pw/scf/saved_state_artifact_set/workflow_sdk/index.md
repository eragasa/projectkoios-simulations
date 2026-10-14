# QE SCF artifact-set Workflow SDK alpha pilot

## Status and scope

This pilot adapts the existing pure
`QeScfSavedStateArtifactSetProjector.action(...)` operation to the independently
installed `projectkoios-workflow-sdk==0.1.0a1` `Firer` boundary. It is an
integration fixture, not a production Workflow binding, release compatibility
promise, artifact-retention operation, or calculator-execution path. The
initial `artifact_set`-as-output shape established bounded alpha evidence; the
current pilot implements the selected owner result shape in which the logical
artifact-set identity is the sole external-state output and the canonical
artifact-set document is SDK evidence.

The exact locally retained SDK pilot wheel is:

- file: `projectkoios_workflow_sdk-0.1.0a1-py3-none-any.whl`;
- SHA-256:
  `925f6974c49c8935ebf2f002b18c86d29375e1b11c3ffc17a29d305fb8095ff4`;
- Workflow repository base commit:
  `63f127dd6922c16accb3dc857cfb2e28224a8958`.

The wheel digest, rather than the base commit alone, identifies this authorized
unreleased SDK candidate because its implementation was built from an
authorized Workflow working-tree candidate. The Simulations dependency metadata
pins the exact alpha version. Isolated pilot verification installs the retained
wheel before installing the Simulations distribution.

## Owner request codec

`QeScfSavedStateArtifactSetProjectionRequestJsonCodec` is a strict,
non-subclassable, Simulations-owned adapter codec. It serializes the existing
`QeScfSavedStateArtifactSetProjectionRequest` without modifying that domain
record or the artifact-set codec.

The request document:

- uses schema identity
  `projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-artifact-set-projection-request:1`;
- uses codec identity
  `projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-artifact-set-projection-request-json:1`;
- carries the exact canonical manifest bytes as strict padded Base64;
- carries ordered member role, domain-relative path, digest, byte size, and
  opaque path-free retention identities;
- carries the already-issued path-free manifest owner identity and
  source-verification evidence identity;
- rejects URL-, URI-path-, absolute-, home-, drive-, dot-relative-, slash-, and
  backslash-shaped private locators at this inline boundary;
- rejects duplicate, unknown, missing, noncanonical, over-deep, oversized, or
  wrongly typed content; and
- reconstructs the existing domain request and requires exact byte-for-byte
  re-encoding.

The SDK alpha hard limit is 4 MiB per inline payload. This pilot applies that
4-MiB bound to the request and artifact-set evidence without reducing or
changing the existing domain codec's 16-MiB contract. The identity output has a
stricter 256-byte ASCII bound.

## Descriptor and binding

`QeScfSavedStateArtifactSetWorkflowFirer` is the Simulations-owned nominal ABC
extending the SDK `Firer`. It retains the SDK's non-overridable `fire(...)`
template and makes the owner `_fire(...)` adapter non-overridable by concrete
projectors. `QeScfSavedStateArtifactSetProjectorFirer` supplies the existing pure
projector operation.

The immutable descriptor advertises:

- firer identity
  `projectkoios.simulations.qe-scf-saved-state-artifact-set.project`;
- input role `projection_request`;
- output role `artifact_set_identity`;
- evidence role `artifact_set`;
- one input, one output, and one evidence value;
- a 4-MiB request and artifact-set evidence bound; and
- a 256-byte artifact-set identity output bound.

The successful result carries exactly one `artifact_set_identity` output and one
`artifact_set` evidence value. The existing domain projector still constructs
and validates its complete result and candidate fragment internally, but the
candidate fragment is not transported because it has no independently accepted
owner codec.

Malformed owner bytes return one correlated `WorkflowFiringRejected` with reason
`invalid_projection_request`. A known pure projection or encoding failure
returns one correlated `WorkflowFiringFailed` with failure
`artifact_set_projection_failed`. Artifact-set evidence above the SDK inline
bound is rejected with
`artifact_set_evidence_exceeds_inline_transport_bound`. No case creates an
ambiguous or effect outcome.

The published transition binding uses these explicitly nonproduction fixture
coordinates:

- definition:
  `projectkoios.workflow.fixture.qe-scf-saved-state-artifact-set:1`;
- transition:
  `projectkoios.workflow.fixture.qe-scf-saved-state-artifact-set-project:1`;
- binding version: `0.1.0a1_fixture.1`.

These coordinates do not claim a current canonical SNAKES export, compiled
Workflow definition, production transition admission, occurrence authority, or
CPN firing. The transition-to-firer binding identity is distinct from the
selected CPN value-binding digest carried by each occurrence context; pilot
tests use an independently domain-separated synthetic selected-binding digest.

## Selected external-output shape

The CPN state value is the Simulations-owned logical
`QeScfSavedStateArtifactSetIdentity`, not the SHA-256 of an SDK inline payload or
SDK document. `QeScfSavedStateArtifactSetIdentityAsciiCodec` encodes it as exact
ASCII bytes with no BOM, whitespace, newline, framing, or trailing bytes and a
256-byte maximum. Its SDK contract uses:

- type
  `projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-artifact-set-identity`;
- schema
  `projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-artifact-set-identity:1`;
- codec
  `projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-artifact-set-identity-ascii:1`;
- representation `canonical-ascii:1`; and
- media type
  `application/vnd.projectkoios.qe-pw-scf-saved-state-artifact-set-identity.v1+ascii`.

Workflow must map the admitted identity value opaquely to the exact CPN string
token; it must not reinterpret the value as a Workflow identity, retention
locator, or SDK payload digest.

The existing canonical `artifact_set` document is SDK evidence. Its exact
payload SHA-256 establishes byte integrity and provenance for those evidence
bytes, but does not become the CPN state identity. The owner logical identity
and artifact-set document payload digest remain deliberately distinct
contracts. This pilot changes only its SDK adapter descriptor, binding, and
result shape; no domain record, semantic-identity profile, artifact-set codec,
or candidate contract changes.

## Preserved domain contracts

The pilot does not modify:

- `saved_state_artifact_set.py`, SHA-256
  `6e1ad5c573dff8c0304157c2ca5eff4d8d0819fbca3efee7ecace84c5226b5d6`;
- `saved_state_candidate.py`, SHA-256
  `d605a8fa30f9da3456a17777c02250eee3666e0b498bdab03a4d8657c5aea6b1`;
- the artifact-set semantic identity profile;
- artifact-set schema, codec, media type, or canonical bytes; or
- the existing candidate schema or canonical wire contract.

The adapter performs no filesystem access, network access, subprocess launch,
QE execution, retention, staging, delivery, scheduling, authority issuance, or
scientific acceptance.

## Remaining Workflow-owned gate

SDK `0.1.0a1` does not define how admitted owner payload bytes become an
identified CPN external-output binding. This pilot therefore stops after the
correlated SDK result. Mapping `artifact_set_identity` opaquely into an exact
selected CPN binding, predecessor revalidation, output/evidence admission,
persistence, and retained firing history remain gated work. Workflow owns
admission and persistence and must fail closed until those contracts are
reviewed and published.
