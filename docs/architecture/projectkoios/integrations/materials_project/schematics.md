# Materials Project integration schematics

## Retrieval and selection

```mermaid
flowchart TD
    credential[Operator-owned API key]
    client[Injected MPRester client]
    request[Explicit elemental query<br/>thermodynamic compatibility scheme]
    entries[Returned candidate entries]
    snapshots[Canonical candidate documents]
    response[Retained candidate response<br/>bytes + SHA-256]
    hull[pymatgen PhaseDiagram.el_refs]
    selected[Selected candidate identity]
    structure[Copied exact structure]
    reference[MaterialsProjectElementalReference]

    credential --> client
    request --> client
    client --> entries
    entries --> snapshots --> response
    entries --> hull --> selected
    selected --> structure
    response --> reference
    selected --> reference
    structure --> reference
```

## Entry and structure identity

```mermaid
flowchart LR
    thermo[Thermo calculation entry<br/>mp-N-suffix]
    canonical[Canonical candidate JSON<br/>retains full calculation identity]
    material[data.material_id<br/>mp-N]
    retrieval[Exact structure retrieval]
    neutral[Immutable PhysKit UnitCell]

    thermo --> canonical
    thermo --> material --> retrieval --> neutral
```

A thermodynamic calculation ID and a material ID are distinct. The full entry
remains in the candidate snapshot; only the canonical `mp-N` material identity
is sent to structure retrieval.

## Snapshot identity

```mermaid
flowchart TD
    snapshot[MaterialsProjectQuerySnapshot]
    criteria[Query parameters]
    time[Retrieval timestamp]
    versions[API, client, and library versions]
    release[Database release or explicit unavailable state]
    candidates[All canonical candidate identities]
    digest[Candidate-response byte size + SHA-256]

    criteria --> snapshot
    time --> snapshot
    versions --> snapshot
    release --> snapshot
    candidates --> snapshot
    digest --> snapshot
```

The candidate-response digest identifies the retained observation, not a later
service state.

## Ni publication path

```mermaid
flowchart TD
    query[Ni + GGA_GGA+U_R2SCAN]
    six[Six retained candidate entries]
    hull[One-element pymatgen hull]
    selected[Selected material mp-23]
    copied[Canonical primitive UnitCell]
    catalog[StructureLibrary record<br/>materials-project.mp-23.primitive]
    local[Separate local spin specification]

    query --> six --> hull --> selected --> copied --> catalog --> local
```

## Local-energy boundary

```mermaid
flowchart LR
    snapshot[Materials Project snapshot]
    phase[Selected phase + external structure]
    catalog[StructureLibrary publication]
    relaxation[Separate local relaxation]
    final[Separate local final energy]
    chemical[Local chemical potential]
    mpenergy[Materials Project energy]
    defect[Local defect formation equation]

    snapshot --> phase --> catalog --> relaxation --> final --> chemical --> defect
    mpenergy --x defect
```

The crossed edge is prohibited.

## Authority and credential boundary

```mermaid
flowchart LR
    operator[Operator]
    credential[Private API credential]
    client[Injected client]
    record[Integration record]
    calculator[Calculator execution]

    operator --> credential --> client
    client --> record
    record --x credential
    record --x calculator
```

The operator creates and scopes the client. Synthetic tests do not contact the
service, and retained records contain no credential.
