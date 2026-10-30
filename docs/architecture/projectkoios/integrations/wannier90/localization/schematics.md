# Planned Wannier90 localization execution schematics

## Route-specific input and sibling evidence closure

```mermaid
flowchart TD
    construction[Exact construction input]
    topology[Authenticated preprocessing topology]
    eig[Authenticated interface eigenvalues]
    amn[Authenticated projections]
    mmn[Authenticated neighbor overlaps]
    ordinary[Closed AMN/MMN/EIG localization input]
    localization[Ordinary localization occurrence]
    unk[Correlated converter-produced UNK inventory]
    consumer[Named downstream wavefunction consumer or native postprocessing mode]

    construction --> ordinary
    topology --> ordinary
    eig --> ordinary
    amn --> ordinary
    mmn --> ordinary
    ordinary --> localization

    unk --> consumer
```

UNK is a correlated sibling extension, not an ordinary localization input.
There is no UNK-to-localization edge. Such an edge may be introduced only by a
separately reviewed, explicitly supported native mode that actually consumes
UNK and declares its staging contract. Without that mode, the localization
runner rejects UNKs as undeclared inputs while downstream composition may still
correlate them with the same parent and construction.

## Future occurrence flow

```mermaid
flowchart TD
    nativeInputs[Closed authenticated native input set]
    prepared[Protected prepared-input evidence]
    authority[Separate external authorization]
    preflight[Future localization provider preflight]
    executor[Existing single-attempt executor]
    process[Retained process evidence]
    outputs[Authenticated route-specific outputs]
    parsers[Existing/supported native parsers]
    provider[Future provider localization observation]

    nativeInputs --> prepared --> preflight
    authority --> preflight
    preflight --> executor --> process --> outputs --> parsers --> provider
```

Prepared inputs and predecessor success are not authority. The future runner
submits at most one localization process. It does not automatically invoke any
other stage.

## Process, convergence, and acceptance

```text
zero return code
  -> process-completion observation
  -> required-output authentication
  -> native parsing
  -> provider-reported localization-status observation
  -> route-level dimensional and lineage correlation
  -> outward neutral adaptation
  -> consumer-owned numerical/scientific assessment
```

Every arrow can terminate in explicit failed or inconclusive evidence. No arrow
is an implication of scientific success. Provider-reported convergence remains
an observation from exact native output, not a ProjectKoios acceptance decision.

## Outward neutral adaptation

```mermaid
flowchart LR
    native[Wannier90 native records]
    provider[Provider localization observation]
    adapter[Separate outward adapter/composition]
    neutral[Neutral localization and representation roles]
    workflow[Planned pw_dft_wannierization contracts]

    native --> provider --> adapter --> neutral --> workflow
    provider -. no import .-> workflow
    workflow -. no import .-> provider
```

The ProjectKoios simulations distribution must provide this first-party
`projectkoios.adapters` surface outside both protected dependency closures,
where it may import both public surfaces. The mapping retains exact source artifact, provider schema, parent,
and adaptation identities. It must not copy native provider objects into
neutral records or reinterpret scientific acceptance.

## Failure and retry isolation

```text
occurrence A inputs -> occurrence A outputs/failure record

retry authorization + new occurrence identity
  -> occurrence B inputs -> occurrence B outputs/failure record
```

Occurrence B does not overwrite A. A restart, if a future route supports it,
adds exact checkpoint lineage and still creates a new occurrence. Partial
native output from A may remain evidence but cannot satisfy B's required roles
unless a reviewed restart contract explicitly binds it.

## Current-status boundary

Current code can parse supported caller-supplied `.wout`, matrix, neighbor, and
Hamiltonian artifacts. The future preflight, runner, staging, output-manifest,
and provider-result boxes do not exist. These diagrams do not create APIs,
authorize execution, stage UNK into ordinary localization, make UNK mandatory,
or establish localization or scientific acceptance.
