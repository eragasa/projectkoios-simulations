# QE SCF saved-state artifact-set projection

## Purpose

This module owns the immutable QE SCF saved-state artifact-set record, its
canonical JSON codec, its retention-independent logical identity derivation, and
the pure projection into the existing candidate saved-state fragment. It does
not import Workflow or create execution, retention, delivery, staging, or
scientific-acceptance authority.

In-process operations pass `QeScfSavedStateArtifactSetRecord`. Canonical bytes
exist only at an explicit encoding or decoding boundary. Retention references
remain separate externally issued values.

## Owner records and references

`QeScfSavedStateArtifactSetRecord` is a frozen, slotted `DataObject` containing:

- SCF calculation and prefix;
- the exact canonical manifest digest and byte size;
- the manifest owner's logical artifact identity;
- an externally issued opaque manifest-retention reference;
- ordered retained-artifact members; and
- an externally issued source-verification evidence identity.

Each `QeScfSavedStateRetainedArtifact` repeats the manifest role, logical
relative POSIX path, SHA-256, and byte size and carries one externally issued
opaque retention reference. The record preserves ordered members and enforces
required QE roles, common prefix save tree, bounded totals, canonical
encodability, and reference-to-byte correlation. The projection request verifies
exact membership and ordering against the supplied canonical manifest bytes.
Shared manifest or member references are permitted only for identical bytes.

The nominal identity and reference types in this module are owner-local. They do
not create a simulations-wide identity taxonomy, dynamically dispatch from
Python classes, or imply that logical identities, payload digests, and retention
references are interchangeable.

## Canonical codec

`QeScfSavedStateArtifactSetCanonicalCodec` has two pure operations:

- `encode(QeScfSavedStateArtifactSetEncodingRequest)` returns canonical JSON
  bytes and exact schema, codec, media-type, byte-length, and payload-SHA-256
  evidence;
- `decode(QeScfSavedStateArtifactSetDecodingRequest)` strictly reconstructs the
  immutable owner record.

The decoder rejects invalid UTF-8, duplicate keys, excessive depth or the
16-MiB canonical-document limit, unknown or missing fields, wrong scalar types,
invalid record invariants, and noncanonical bytes. Public request and result
records validate their own exact correlations even when directly reconstructed.

The payload digest is SHA-256 over canonical payload bytes only. The payload
must not embed its own digest, a future transport envelope, or an envelope
identity.

## Logical identity

`QeScfSavedStateArtifactSetIdentityDeriver.action(...)` derives
`QeScfSavedStateArtifactSetIdentity` from a separate, versioned canonical
semantic projection. Its preimage includes:

- the identity-profile identifier;
- calculation and prefix;
- manifest digest and byte size; and
- ordered artifact role, relative path, digest, and byte size.

It excludes retention references, the manifest owner's separately issued
artifact identity, source-verification evidence identity, Workflow correlation,
authority, transport metadata, and the logical identity itself. Consequently,
relocating identical saved-state bytes or obtaining new verification evidence
does not change saved-state semantics, while changing an ordered member's
content does.

The logical semantic digest and canonical payload digest are deliberately
separate. Codec or transport changes must not silently redefine the logical
artifact-set identity.

## Projection

`QeScfSavedStateArtifactSetProjector.action(...)` consumes:

- one `QeSavedStateManifest`;
- its exact canonical manifest bytes;
- already-issued manifest and member retention references;
- the manifest owner's artifact identity; and
- source-verification evidence identity.

It returns the immutable artifact-set object, its provider-owned logical
identity, and the exact existing `QeScfCandidateSavedState` fragment. The
projector does not serialize the record as an in-process substitute, locate
files, inspect directories, copy bytes, retain artifacts, or issue supplied
references or evidence identities.

## Bounds and failure behavior

The boundary fails closed when:

- manifest bytes are not the exact canonical encoding of the supplied manifest;
- the calculation is not SCF;
- retained role, path, digest, size, count, or order differs from the manifest;
- a reference or identity is non-ASCII, unbounded, contains controls, is a file
  URI, or is an absolute, home-relative, drive-relative, dot-relative,
  unqualified slash-relative, or backslash machine path;
- more than 4096 artifacts or 256 pseudopotentials are declared;
- a pseudopotential filename exceeds 255 ASCII bytes;
- a logical relative path exceeds 512 UTF-8 bytes or contains a non-UTF-8
  scalar value;
- typed manifest string content cannot fit the 16-MiB canonical JSON budget,
  before manifest serialization, or canonical manifest/artifact-set payload
  bytes exceed 16 MiB;
- declared saved-state bytes exceed 64 GiB;
- one retention reference aliases different bytes; or
- a public result is reconstructed with mismatched request, record, identity,
  payload, or candidate data.

The module has no filesystem or subprocess capability and performs no QE
execution or external calculation.

## Relationship to Workflow

No accepted versioned Workflow opaque-artifact envelope is currently consumed.
Future integration must adapt through Workflow's reviewed public contract rather
than freezing a guessed field layout here. The requirements under review include
owner/type/schema/codec/representation metadata, exact payload length and
digest, and an opaque retention reference, but those are not an approved
Workflow API.

The required acyclic ordering is:

1. immutable owner object and owner logical identity;
2. canonical payload bytes;
3. payload byte length and SHA-256;
4. external retention and its independently issued reference;
5. future transport envelope; and
6. optional envelope identity derived from a preimage that excludes itself.

Workflow validates and carries an accepted opaque reference; it does not import
or reconstruct this simulations-owned Python object.

The separately bounded [Workflow SDK alpha pilot](workflow_sdk/) transports the
existing pure projection request, emits the owner logical artifact-set identity
as its sole external-state output, and carries the artifact-set canonical bytes
as SDK evidence under the SDK's inline limits. It does not define a
retained-reference envelope or the Workflow-owned mapping from the admitted
owner identity to a CPN external-output binding.
