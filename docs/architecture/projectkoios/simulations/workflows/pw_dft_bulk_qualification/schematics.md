# Plane-wave DFT bulk qualification schematics

## Layer and authority boundary

```mermaid
flowchart LR
    consumer[Consuming scientific project]
    tool[tools/pw_dft_bulk_qualification]
    adapter[projectkoios.adapters]
    bulk[Planned neutral bulk qualification]
    scf[pw_dft_scf]
    relax[pw_dft_relaxation]
    core[Protected simulation core]
    providers[Outward provider integrations]
    runtime[External Workflow runtime]
    authority[External per-occurrence authorization]

    consumer -->|exact declarations and policy| tool
    tool --> bulk
    tool --> adapter
    adapter -->|neutral public contracts| bulk
    adapter --> providers
    bulk --> scf
    bulk --> relax
    bulk --> core
    scf --> core
    relax --> core
    runtime -->|scheduling and persistence| tool
    authority --> tool

    bulk -. forbidden import .-> adapter
    bulk -. forbidden import .-> providers
    bulk -. forbidden import .-> runtime
    core -. forbidden import .-> bulk
```

Arrows into neutral workflow packages are calls through public contracts, not
permission for those packages to import outward callers. Provider selection and
native mapping remain outside the workflow dependency closure.

## Scientific dependency and feedback

The route below is a requirements/evidence graph. No arrow starts a calculator
or grants successor authority.

```mermaid
flowchart TD
    s0[Exact seed structure S0]
    study0[Joint cutoff and reciprocal-sampling study]
    q0[Provisional qualification Q0 at S0]
    relax1[Relaxation requirement under Q0]
    s1[Mechanically qualified structure S1]
    confirm[Fresh confirmation study on current S_i]
    decision{Candidate setting unchanged and confirmed?}
    accepted[Accepted exact pair S* and Q*]
    changed[Changed setting Q1 at S1]
    rerelax[New relaxation under Q1]
    s2[New mechanically qualified structure S2]
    budget{Feedback budget available?}
    inconclusive[Inconclusive or budget exhausted]

    s0 --> study0 --> q0 --> relax1 --> s1 --> confirm --> decision
    decision -->|yes| accepted
    decision -->|no; tighter or different setting| changed --> budget
    budget -->|yes| rerelax --> s2 --> confirm
    budget -->|no| inconclusive
```

`Q0@S0` is not rewritten as `Q0@S1`. `S1` is not silently accepted under a
changed `Q1`. Each changed structure, setting, specification, and occurrence
has a distinct identity. The diagram abbreviates repeated iterations; the
actual lineage remains acyclic even though the composition rule feeds a new
iteration.

## Existing grid assessment after a changed cell

```text
exact lattice S_i
  + existing PwDftScfGridConvergenceRecipe and policy
  + neutral wavefunction/density-potential cutoff realization
  + adapter proof for every exact projected input
  -> typed structure/request/occurrence/evidence correlation
  -> accepted existing coordinate and full k-point policy K_i
```

The existing grid assessment is rerun on every relaxed structure, but it becomes
`Q_i@S_i` only through the new typed correlation around its observations and
assessment. Equal integer mesh tuples before and after relaxation remain
separate evidence and require fresh confirmation; no new reciprocal-density
coordinate is introduced.

## Per-occurrence authorization

```mermaid
sequenceDiagram
    participant C as Neutral composition
    participant R as External runtime
    participant O as Outward tool/adapter
    participant E as Single-attempt executor
    participant P as Provider process

    C-->>R: non-authorizing child requirement
    R->>R: obtain explicit authority for this occurrence
    R->>O: admit one provider-bound occurrence
    O->>E: submit one authorized request
    E->>P: start at most one process
    P-->>E: native output
    E-->>O: retained terminal evidence
    O-->>C: normalized exact observation
    C-->>R: next requirement or terminal decision
```

A retry is a new occurrence. Completion of the provisional study does not
authorize relaxation; relaxation completion does not authorize confirmation;
and a failed confirmation does not authorize re-relaxation.

## Gate to the Wannier route

```text
accepted exact pair (S*, Q*)
  -> exact parent-SCF requirement
  -> exact parent evidence
  -> NSCF
  -> Wannier90 preprocessing
  -> pw2wannier90 interface generation
  -> Wannier90 localization
```

Bulk qualification is a predecessor campaign. The later Wannier route remains
five calculator occurrences beginning with a new parent SCF after pair
acceptance. The confirmation occurrence remains predecessor evidence and is not
reused as the parent by this architecture.

## Status

These diagrams do not define an executable topology, public API, queue,
transition guard, retry rule, executable identity, or authorization token. They
do not show that an adapter, tool, provider capability, qualified structure, or
scientifically accepted route currently exists.
