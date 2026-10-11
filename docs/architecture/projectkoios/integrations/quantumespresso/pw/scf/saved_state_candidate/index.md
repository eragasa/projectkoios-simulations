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

## Pure encoding boundary

`QeScfSavedStateCandidateJsonCodec`:

1. consumes immutable typed records;
2. produces exact canonical control-JSON bytes and owner encoding metadata;
3. performs no artifact retention, filesystem, network, clock, random,
   calculator, or authority operation; and
4. rejects noncanonical bytes, duplicate or unknown keys, invalid types,
   machine paths, and bounded-field violations.

An outer authorized artifact boundary must retain the returned bytes. Generic
Workflow, not this provider module, assembles and admits the six-field payload
reference using the immutable artifact identity returned by that boundary.

`QeScfSavedStateCandidateVerifier` checks the candidate against the exact
canonical saved-state manifest bytes, `CalculatorInputRecord`, path-free
`SimulationEvidenceRecord`, and existing `PwDftScfWorkflowSucceeded` outcome.
It verifies rendered-input, structure, executable, pseudopotential, manifest,
evaluation, task, completion, and convergence correlations. Artifact-store
resolution and source-byte verification remain isolated worker operations.

The codec requires `workflow.child_export_identity`, so changing or omitting the
linked immutable child export changes or invalidates the candidate identity.
The provider verifier does not resolve Workflow plans or terminal deliveries and
must not accept a caller-asserted export as proof. Generic Workflow separately
checks that this field equals the export selected by the retained child plan and
terminal delivery.

## Hierarchical delivery

The Generic Workflow conformance target is
`projectkoios.workflow.cpn-bindings@0.1.0`, contract SHA-256
`e6428a8b0d8a47d4f9a6596300fe5ccc65bb16c12e1cc8ffe64884720bd513c2`.
A successful SCF delivery requires the existing terminal payload first and one
candidate companion at requirement ordinal `0`, retained in phase
`post_terminal_pre_delivery_retained`. Known-failure classifications declare an
empty companion tuple. The companion is not a CPN token and does not add or
change any place, transition, arc, guard, expression, or marking.

The canonical SNAKES-to-Workflow exporter, compiled plan/export identities,
golden parity fixture, artifact-store binding, and nested runtime integration
remain unavailable. Their identities must be derived from future exact bytes;
this module does not fabricate nominal substitutes.
