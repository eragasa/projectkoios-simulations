# Plane-wave DFT defect-formation workflow schematics

## End-to-end study composition

```mermaid
flowchart TD
    subgraph references[Elemental-reference qualification]
        siConv[Si primitive numerical convergence]
        siConfirm[Conventional-host confirmation]
        siRelax[Si zero-pressure host relaxation]
        siFinal[Si final SCF and evidence]
        muSi[Local chemical potential mu_Si]

        bConv[B mp-160 numerical convergence]
        bRelax[B zero-pressure relaxation]
        bFinal[B final SCF and evidence]
        muB[Local chemical potential mu_B]

        pConv[P mp-568348 numerical convergence]
        pRelax[P zero-pressure relaxation]
        pFinal[P final SCF and evidence]
        muP[Local chemical potential mu_P]

        siConv --> siConfirm --> siRelax --> siFinal --> muSi
        bConv --> bRelax --> bFinal --> muB
        pConv --> pRelax --> pFinal --> muP
    end

    publish[Publish exact relaxed Si host]
    sizes[Replicate pristine 64, 216, and 512 atom cells]
    pristine[Matched pristine final SCF per size]

    subgraph phosphorus[Si:P start ensemble per size]
        pStarts[Ideal, &lt;100&gt;, and &lt;111&gt; starts]
        pPre[Qualified lower-cost pre-relaxation]
        pProd[Production fixed-cell relaxation]
        pScf[Separate production final SCF]
        pBasin[Lowest compatible observed basin]
        pStarts --> pPre --> pProd --> pScf --> pBasin
    end

    subgraph boron[Si:B start ensemble per size]
        bStarts[Ideal, &lt;100&gt;, and &lt;111&gt; starts]
        bPre[Qualified lower-cost pre-relaxation]
        bProd[Production fixed-cell relaxation]
        bScf[Separate production final SCF]
        bBasin[Lowest compatible observed basin]
        bStarts --> bPre --> bProd --> bScf --> bBasin
    end

    compatible[Exact evidence and compatibility qualification]
    formation[Neutral formation energies by dopant and size]
    stress[Fixed-host residual stress by dopant and size]
    sizePolicy[Independent 64 to 216 to 512 stability policies]
    outcome{Study outcome}
    accepted[Criterion satisfied]
    extend[Additional size required]
    inconclusive[Inconclusive or rejected]
    exhausted[Budget exhausted]

    siFinal --> publish --> sizes
    sizes --> pristine
    sizes --> pStarts
    sizes --> bStarts
    pristine --> compatible
    pBasin --> compatible
    bBasin --> compatible
    muSi --> compatible
    muB --> compatible
    muP --> compatible
    compatible --> formation
    compatible --> stress
    formation --> sizePolicy
    stress --> sizePolicy
    sizePolicy --> outcome
    outcome --> accepted
    outcome --> extend
    outcome --> inconclusive
    outcome --> exhausted
```

Every relaxation or SCF node is a separate one-simulation occurrence. No handoff
authorizes calculator execution.

## Reuse boundary

```mermaid
flowchart LR
    defect[pw_dft_defect_formation]
    relax[pw_dft_relaxation public composition]
    scf[pw_dft_scf public recipes and results]
    dftDefects[simulations.dft.defects qualification]
    defects[simulations.defects derivations]
    library[SimulationLibrary and evidence]
    structure[Structure records and defect deltas]
    providers[QE or VASP integrations]
    outward[Outward tools or applications]

    defect --> relax
    defect --> scf
    defect --> dftDefects --> defects
    defect --> library
    defect --> structure
    defect --x providers
    outward --> defect
    outward --> providers
```

Outward composition binds neutral integration identifiers to provider
implementations. The production defect workflow remains provider-independent.

## Matched size series

```mermaid
flowchart LR
    si64[Pristine Si 64]
    si216[Pristine Si 216]
    si512[Pristine Si 512]
    p64[Si:P 64 selected basin]
    p216[Si:P 216 selected basin]
    p512[Si:P 512 selected basin]
    b64[Si:B 64 selected basin]
    b216[Si:B 216 selected basin]
    b512[Si:B 512 selected basin]
    refs[Common compatible local Si, B, and P references]
    assess[Formation-energy and residual-stress assessments]

    si64 --> assess
    si216 --> assess
    si512 --> assess
    p64 --> assess
    p216 --> assess
    p512 --> assess
    b64 --> assess
    b216 --> assess
    b512 --> assess
    refs --> assess
```

Each defect energy is paired with the pristine cell of the same exact supercell
transformation. Optional full-cell release evidence remains a separately
labelled finite-concentration diagnostic.

## One defect-start chain

```mermaid
flowchart TD
    start[Exact declared defect start]
    pre[Lower-cost qualified fixed-cell pre-relaxation]
    lineage[Exact pre-relaxation output lineage]
    production[Production-cutoff fixed-cell relaxation]
    final[Separate production final SCF]
    evidence[Energy, force, stress, and magnetization evidence]
    noReject[No basin rejection from approximate pre-relaxation energy]

    start --> pre --> lineage --> production --> final --> evidence
    pre -. qualification .-> noReject
    noReject --> production
```

The production relaxation converges again at the final numerical settings. A
single high-cutoff energy correction on the pre-relaxed geometry is not a
production relaxation.

## Runtime boundary at concurrency one

```mermaid
sequenceDiagram
    participant C as Scientific composition
    participant W as External Workflow runtime
    participant E as Single-simulation executor
    participant P as Provider calculator

    C->>W: non-authorizing child requirement
    W->>W: obtain explicit authority and admit occurrence
    W->>E: execute one child request
    E->>P: start one calculator process
    P-->>E: native output
    E-->>W: live output plus terminal record
    W-->>C: normalized immutable evidence
    Note over W,E: Runtime admits the next child only after this return
```

Occurrence identity, queues, leases, retries, cancellation, authority, and
durable delivery belong to the external runtime. Scientific composition owns
which child is required and how normalized evidence is assessed.

## Future topology rule

```mermaid
flowchart LR
    composition[Composition and policy records]
    inventory[Name inventory]
    topology[Executable Petri-net topology]
    complete[Reviewed places, transitions, arcs, guards, tokens, and occurrences]

    composition --x topology
    inventory --x topology
    complete --> topology
```

Documentation and name inventories do not establish executable topology. If a
topology is introduced, exactly one reviewed source remains authoritative until
a separately reviewed generic Workflow extraction replaces it.
