# Materials Project integration implementation rules

## Current modules

```text
src/python/projectkoios/integrations/materials_project/
  __init__.py
  contracts.py
```

The current injected-client boundary, immutable structure copying, canonical
candidate snapshots, and synthetic tests are authoritative. No client or record
retains an API key.

## Snapshot records

Frozen, slotted records represent:

- query and retrieval metadata;
- canonical candidate-entry observations;
- complete candidate-set artifact identity; and
- selection correlation between request, candidate set, pymatgen hull result,
  and copied structure.

`MaterialsProjectCandidateSnapshot` retains each canonical entry document.
`MaterialsProjectQuerySnapshot` retains exact query criteria, sorted candidates,
source response order, response digest, retrieval time, client implementation,
mp-api and pymatgen versions, and a database release only when the injected
client exposes one. No record contains an API key or reusable credential.

## Canonical candidate snapshot

Every returned entry must be adapted into a strict versioned neutral document
containing the fields used by hull construction and audit, including entry ID,
composition, uncorrected and corrected energy information supplied by the
entry, correction/adjustment data, thermo type when represented, and structure
identity when available. Unknown or unsupported entry forms fail rather than
being omitted from the digest.

The candidate documents are sorted by a schema-defined exact key, encoded as
UTF-8 canonical JSON, and hashed as one candidate-set artifact. The original
entry order and candidate count are retained separately. This prevents list
ordering alone from changing scientific meaning while preserving what the API
returned.

The snapshot records the mp-api and pymatgen versions. It records Materials
Project database/release identity only when supplied by the service; no Git
revision, material ID, or retrieval date is relabeled as a database revision.

## Selection correlation

`MaterialsProjectElementalReferenceSelector` returns a reference containing:

- exact request;
- retrieval snapshot identity;
- selected candidate identity;
- selected Materials Project material ID;
- energy per atom and hull distance used in selection;
- complete candidate count;
- exact copied structure bytes; and
- hull construction implementation/version evidence.

Selection must prove that the chosen entry occurs in the retained candidate
snapshot and that its copied structure matches the selected material ID.

## Structure-library publication

Publishing the copied structure creates a transferred/external-snapshot
`StructureRecord`. Provenance identifies the Materials Project snapshot,
selected candidate, exact structure bytes, and adaptation schema. When no
immutable database revision exists, provenance says so explicitly and uses the
retained response digest as the exact observation identity.

The published geometry remains an external reference, not a locally relaxed
production input. Local relaxation receives a new specification and evidence.

## Required verification

Tests must cover stable candidate ordering, changed energy/correction/entry
identity, changed candidate membership, missing database revision, selected
entry absence, structure/material mismatch, disordered sites, malformed query
metadata, client/library versions, exact snapshot round trips, and absence of
credentials and live network access.
