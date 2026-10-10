# Materials Project integration schematics

## Retrieval and selection

```text
operator-owned API key + injected client
                    |
                    v
explicit elemental query + thermo scheme
                    |
                    v
returned candidate entries
                    |
                    +--> canonical candidate documents
                    |              |
                    |              v
                    |    retained snapshot bytes + SHA-256
                    |
                    v
pymatgen PhaseDiagram.el_refs
                    |
                    v
selected candidate + copied exact structure
                    |
                    v
MaterialsProjectElementalReference
```

## Snapshot identity

```text
MaterialsProjectRetrievalSnapshot
  query parameters
  retrieval timestamp
  API/client/library versions
  database/release ID when available
  all canonical candidate identities
  candidate-set byte size + SHA-256
```

A missing database revision remains explicitly unavailable. The candidate-set
digest identifies the retained response, not future service state.

## Local-energy boundary

```text
Materials Project snapshot
       |
       v
selected phase identity and external structure
       |
       v
StructureLibrary publication
       |
       v
separate local relaxation + final energy calculation
       |
       v
local chemical potential
```

```text
Materials Project energy --------X--------> local defect formation equation
```

The crossed edge is prohibited.

## Authority and credential boundary

```text
integration record -X-> API credential retention
integration record -X-> automatic network request
integration record -X-> calculator execution authority
```

The operator creates and scopes the client. Synthetic tests do not contact the
service.
