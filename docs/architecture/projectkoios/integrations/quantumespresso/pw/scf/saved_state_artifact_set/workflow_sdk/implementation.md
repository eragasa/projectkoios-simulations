# Implementation

## SDK owner boundary

`src/python/projectkoios/integrations/quantumespresso/pw/scf/saved_state_artifact_set_workflow.py`
contains the Simulations-owned pure-firing boundary:

- `QeScfSavedStateArtifactSetProjectionRequestJsonCodec` strictly encodes and
  decodes the existing immutable projection request;
- `QeScfSavedStateArtifactSetIdentityAsciiCodec` carries only the owner logical
  identity into CPN state;
- `QeScfSavedStateArtifactSetWorkflowFirer` is the nominal owner ABC;
- `QeScfSavedStateArtifactSetProjectorFirer` invokes the existing pure domain
  projector; and
- `QeScfSavedStateArtifactSetProjectorIntegration` exposes the exact firer and
  deployment-supplied distribution identity through the SDK worker composition
  root.

The integration module depends only on the standalone Workflow SDK, not the
Workflow service, CPN kernel, runtime, or persistence implementation.

## Owner source authority adapter

`src/python/projectkoios/adapters/workflow/quantumespresso/pw/scf/saved_state_artifact_set.py`
is the outward adapter for the experimental Workflow runtime source port. It is
kept outside the protected simulation core and reusable simulation-workflow
contracts.

`QeScfSavedStateProjectionRequestSourceRepository`:

1. encodes the owner request with the strict owner codec;
2. derives a SHA-256 content identity;
3. writes a private temporary file with mode `0600`, flushes it, and atomically
   links the immutable revision into a private content-addressed directory;
4. never replaces an existing revision;
5. resolves only the exact source kind, profile, and opaque source identity;
6. performs a bounded no-follow regular-file read;
7. checks the filename digest and exact canonical owner decoding; and
8. constructs Workflow source evidence only from the repository-loaded bytes.

Private paths never enter the source reference, SDK request, compact commit, CPN
transcript, or replay API. External mutation is detected as corruption; callers
cannot use this adapter API to replace an existing content revision.

The adapter imports the unreleased experimental Workflow runtime and therefore
requires the explicit `workflow-runtime` optional dependency and a composed
candidate environment. The base Simulations distribution still depends only on
the standalone SDK. The current `projectkoios-workflow==0.0.0` pin identifies an
unreleased local candidate and is not a released compatibility promise.

## Verified vertical slice

The cross-repository test
`tests/projectkoios/adapters/workflow/quantumespresso/pw/scf/test__QeScfSavedStateWorkflowRuntime.py`
constructs one actual CPN transition and executes:

1. immutable owner request retention;
2. CPN enablement and deterministic binding selection;
3. repository-authorized SDK request construction;
4. durable predecessor reservation;
5. validated worker integration invocation of the real QE artifact-set
   projector;
6. opaque ASCII owner-identity admission;
7. pure CPN firing;
8. atomic SQLite reservation consumption, compact commit, CPN evidence, lifecycle
   transition, and marking advancement;
9. compact replay;
10. durable pure CPN refiring;
11. reservation-lifecycle replay; and
12. bounded committed safety-state reconstruction.

After commit, the test removes the owner source directory before all replay
operations. The counting owner firer remains at exactly one invocation. The
owner request and canonical artifact-set evidence bytes are absent from the
Workflow SQLite database. The logical artifact-set identity remains present in
CPN state by design.

This proves a bounded pure-action path, not calculator execution, OS-process
worker isolation, complete scheduler replay, full CPN-bindings conformance, or
effectful lifecycle behavior.
