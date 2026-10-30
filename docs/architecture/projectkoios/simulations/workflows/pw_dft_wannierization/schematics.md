# Plane-wave DFT Wannierization workflow schematics

## Layer and dependency boundary

The planned workflow layer points inward only. The ProjectKoios simulations
repository owns first-party provider selection and route invocation in
`tools/pw_dft_wannierization`, and native/neutral mapping in an outward
`projectkoios.adapters` surface.

```mermaid
flowchart LR
    consumer[Consuming scientific project]
    tool[tools/pw_dft_wannierization]
    adapter[projectkoios.adapters]
    workflow[Planned neutral pw_dft_wannierization contracts]
    bulk[Planned neutral bulk qualification contracts]
    core[Protected simulation core]
    qe[Quantum ESPRESSO integration]
    w90[Wannier90 integration]
    runtime[External Workflow runtime]
    authority[External per-occurrence authorization]

    consumer -->|exact declarations and policy| tool
    tool -->|neutral requirements and normalized evidence| workflow
    tool --> adapter
    adapter -->|neutral public contracts| workflow
    adapter --> qe
    adapter --> w90
    workflow --> bulk
    workflow --> core
    bulk --> core
    runtime -->|scheduling and persistence| tool
    authority --> tool

    workflow -. forbidden import .-> qe
    workflow -. forbidden import .-> w90
    workflow -. forbidden import .-> runtime
    core -. forbidden import .-> workflow
    core -. forbidden import .-> bulk
```

The arrows into `workflow` are calls through its public neutral contracts, not
permission for it to import the callers. The protected core does not depend on
the workflow layer. Outward integrations may depend on protected-core ports but
must not import workflow policy in production provider modules.

## Planned scientific route

The following diagram is a requirements and evidence flow. It is not an
executable topology and does not authorize any arrow.

```mermaid
flowchart TD
    accepted[Accepted exact bulk structure and setting pair]
    parent[Qualified plane-wave parent evidence]
    frame[Uniform-grid Bloch-frame requirement]
    nscf[Normalized NSCF evidence]
    preprocess[Localization-preprocessing requirement]
    topology[Normalized neighbor-topology evidence]
    interface[Plane-wave interface requirement]
    interfaceEvidence[Normalized interface evidence]
    localization[Localization requirement]
    localizationEvidence[Normalized localization observation]
    representation[Correlated representation evidence]
    assessment[Consumer-owned comparison and acceptance]

    accepted --> parent
    parent --> frame
    frame --> nscf
    nscf --> preprocess
    preprocess --> topology
    nscf --> interface
    topology --> interface
    interface --> interfaceEvidence
    interfaceEvidence --> localization
    localization --> localizationEvidence
    parent --> representation
    nscf --> representation
    topology --> representation
    interfaceEvidence --> representation
    localizationEvidence --> representation
    representation --> assessment
```

The accepted bulk pair is produced by a separate predecessor campaign with
seed-bound numerical convergence, zero-pressure relaxation, and fresh
final-setting confirmation. It is not an additional hidden occurrence in this
five-occurrence route.

Each evidence node retains exact predecessor identities. No later node may be
constructed merely because expected filenames are present. The representation
must remain traceable to the exact parent state, uniform grid, construction
declaration, normalized interface observations, and localization observation.

## Native adaptation boundary

The neutral workflow names roles by meaning. The first-party adapter maps those
roles to provider-native calculations and artifacts, while the repository tool
invokes the complete route:

```text
neutral parent-state requirement
  -> outward QE SCF binding
  -> exact generic execution/evidence records
  -> neutral parent-state evidence

neutral uniform-grid requirement
  -> outward QE NSCF binding
  -> provider-native saved state and QEXSD parsing
  -> neutral Bloch-frame evidence

neutral preprocessing/interface/localization requirements
  -> future outward Wannier90 preprocessing binding
  -> outward QE pw2wannier90 binding
  -> future outward Wannier90 localization binding
  -> neutral topology, interface, and localization observations

optional declared component-operator requirement
  -> provider-owned coefficient or UNK-bearing route
  -> distinct verified coefficient or sampled-wavefunction observation
  -> explicit transform evidence when the consumer needs another representation
```

The optional extension is absent from a spectral-only profile; its provider
artifacts must not be inferred from basenames or imposed on every route. UNK
samples are not silently relabeled as plane-wave coefficients.

The current Wannier90 integration can authenticate and parse caller-supplied
native text artifacts. The preprocessing and localization binding arrows are
future prerequisites, not current APIs. Adding them requires reviewed outward
architecture and implementation; adding this workflow documentation alone does
not make them available.

## Occurrence and authority flow

Every calculator process is a distinct occurrence admitted outside the neutral
workflow package. The sequence below applies to each of the five route
occurrences after bulk qualification; predecessor qualification occurrences are
separately admitted under their own composition.

```mermaid
sequenceDiagram
    participant C as Consumer policy
    participant R as External runtime
    participant O as Outward composition
    participant W as Neutral workflow contracts
    participant E as Single-attempt executor
    participant A as Retained artifacts

    C->>W: provide exact declaration and available evidence
    W-->>C: return requirement or non-authorizing handoff
    C->>R: request one bounded occurrence
    R->>R: obtain and verify external execution authority
    R->>O: admit one provider-bound occurrence
    O->>E: submit one authorized execution request
    E->>A: retain stdout, stderr, native files, and terminal record
    E-->>O: return or raise with terminal execution evidence
    O->>W: adapt provider evidence to neutral observations
    W-->>C: return correlation or next requirement
```

The neutral workflow never performs the `R->>R` authority step and never sets
execution authorization. A completed occurrence does not automatically admit
the next occurrence. A failure or inconclusive observation remains retained
evidence and produces no implicit retry.

## Identity chain

A final representation evidence record must preserve a directed acyclic
identity chain rather than a mutable “current result” pointer:

```text
accepted bulk qualification identity
  + exact accepted structure identity
  + exact final numerical-setting identity
      -> parent specification identity
          + prepared-parent-input identity
          + parent occurrence/evidence identity
              -> uniform-grid declaration and evidence identity
                  -> preprocessing declaration and topology identity
                  -> interface declaration and evidence identity
                      -> localization declaration and observation identity
                          -> representation-evidence identity
```

A provisional `Q0@S0` cannot satisfy the accepted-bulk role. If final
confirmation changes the setting on a relaxed structure, the bulk composition
must re-relax and reconfirm before it can publish the predecessor identity used
above.

Changing a structure, pseudopotential, reciprocal grid, band inventory, spin
branch, construction declaration, or provider-native artifact creates a new
identity. It must not rewrite an earlier node or inherit acceptance from it.
Locations are storage references rather than scientific identity; portable
records use exact byte size and digest where artifact bytes are external.

## Status and nonclaims

These diagrams inventory intended boundaries only. They do not define a
complete Petri net, prove that an adapter exists, identify executable paths,
establish native artifact availability, promise dimensional compatibility, or
show that a real route has completed. No diagram grants calculator authority,
numerical convergence, localization convergence, scientific validation, or
publication acceptance.
