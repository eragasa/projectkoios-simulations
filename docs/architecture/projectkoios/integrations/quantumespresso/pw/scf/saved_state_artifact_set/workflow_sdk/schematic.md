# Schematic

```mermaid
flowchart LR
    Request[Typed QE projection request]
    OwnerStore[Owner-private immutable source repository]
    Reference[Opaque source reference]
    Authority[Workflow source authorization]
    Selected[Exact selected CPN binding]
    SDKRequest[Canonical SDK request]
    Worker[Validated QE worker integration]
    Projector[Pure artifact-set projector]
    Identity[Owner logical identity output]
    Evidence[Canonical artifact-set evidence]
    CPN[Pure CPN transition firing]
    Atomic[(Atomic Workflow SQLite commit)]
    Compact[Compact replay]
    Refire[Durable CPN refiring]
    Lifecycle[Lifecycle replay]
    Safety[Safety-state reconstruction]

    Request -->|canonical owner bytes| OwnerStore
    OwnerStore --> Reference
    Reference --> Authority
    Selected --> Authority
    Authority --> SDKRequest
    SDKRequest --> Worker
    Worker --> Projector
    Projector --> Identity
    Projector --> Evidence
    Identity -->|opaque ASCII value| CPN
    Selected --> CPN
    CPN --> Atomic
    Evidence -. admitted identity references only .-> Atomic
    Atomic --> Compact
    Atomic --> Refire
    Atomic --> Lifecycle
    Atomic --> Safety

    OwnerStore -. not invoked .-> Compact
    Worker -. not invoked .-> Compact
    OwnerStore -. not invoked .-> Refire
    Worker -. not invoked .-> Refire
    OwnerStore -. not invoked .-> Lifecycle
    Worker -. not invoked .-> Lifecycle
    OwnerStore -. not invoked .-> Safety
    Worker -. not invoked .-> Safety
```

Private owner payload bodies and filesystem locators stop at the owner boundary.
Workflow durably retains compact identities, admitted source-authority
references, canonical CPN transcript evidence, lifecycle state, and markings.
