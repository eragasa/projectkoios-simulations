# Planned Wannier90 preprocessing schematics

## Provider occurrence flow

The diagram describes a future provider occurrence, not current executable
behavior.

```mermaid
flowchart TD
    declaration[Caller-owned exact construction declaration]
    render[Future deterministic native render or exact input binding]
    prepared[Protected prepared-input record]
    authority[Separate external execution authorization]
    preflight[Future provider preflight]
    executor[Existing single-attempt executor]
    native[Retained native stdout, stderr, and topology artifact]
    parse[Existing native topology parser]
    observation[Future provider preprocessing observation]

    declaration --> render --> prepared
    prepared --> preflight
    authority --> preflight
    preflight --> executor --> native --> parse --> observation
```

Neither the declaration nor prepared input carries reusable authority. The
future provider preflight verifies exact executable and input identities, but
it does not create authority. The existing executor starts at most one process
for the occurrence.

## Render-only branch

```text
exact construction declaration
  -> validate provider-native values
  -> render or authenticate exact input bytes
  -> retain prepared-input identity and expected output roles
  -> stop
```

Render-only operation stops before executable resolution, output-process
creation, or native execution. It may be used by tests and inspection tools,
but it does not establish that an input is scientifically accepted.

## Native and neutral boundary

The provider output remains native until an outward composition maps it to a
neutral role:

```mermaid
flowchart LR
    provider[Wannier90 preprocessing integration]
    native[Authenticated native topology record]
    adapter[Separately reviewed outward adapter]
    neutral[Neutral preprocessing/topology role]
    workflow[Planned pw_dft_wannierization contracts]

    provider --> native --> adapter --> neutral --> workflow
    provider -. forbidden import .-> workflow
    workflow -. forbidden import .-> provider
```

The adapter is not implemented by this documentation. The ProjectKoios
simulations distribution must provide it through a reviewed first-party outward
`projectkoios.adapters` surface; consuming applications may reuse the same
public contracts.
It imports public contracts from both sides and records the exact mapping. It
does not cause either production owner to import the other.

## Success and failure separation

```text
process returned zero
  != required topology artifact authenticated
  != native topology parsed
  != construction declaration correlated
  != neutral handoff assembled
  != scientific construction accepted
```

Each equality is intentionally false. A later stage may consume only the
specific verified predecessor required by its contract. Missing or inconsistent
evidence produces a requirement, rejection, or inconclusive outcome; it does
not trigger an automatic converter or localization process.

## Occurrence isolation

A future output layout may retain separate input, process, and artifact
manifests, but its exact schema is not fixed here. The invariants are:

- a new occurrence uses a new nonsymlink output directory;
- staged input bytes are immutable for that occurrence;
- stdout and stderr remain separate retained artifacts;
- the terminal execution record is written before a process result is exposed;
- the topology artifact is authenticated before parsing;
- partial failure artifacts remain associated with the failed occurrence; and
- retries never replace an earlier occurrence.

## Status boundary

The boxes labeled “future” do not correspond to present public APIs. Current
ProjectKoios can parse caller-supplied supported Wannier90 artifacts, but it
does not render preprocessing input or invoke `wannier90.x -pp`. These diagrams
do not alter that parser-only status, grant execution authority, or establish
numerical or scientific acceptance.
