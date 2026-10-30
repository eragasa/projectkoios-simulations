# Plane-wave DFT SCF workflow schematics

## Campaign and recipe flow

```text
neutral base request + campaign identity
                    |
                    v
       single / k-point / cutoff / grid recipe
                    |
                    +--> one immutable request
                    `--> ordered convergence coordinates -> child requests
```

## Single-result comparison

```text
successful left child result ----+
                                  +-> explicit alignment -> pure comparator
successful right child result ---+                         |
                                                            v
                                             qualified comparison analysis
```

The comparator rejects incomplete or unconverged results. Native comparison is
explicitly descriptive; reference alignment requires declared metadata.

## Convergence loop

```text
ordered normalized observations
              |
              v
          assessor + policy
              |
              v
     convergence assessment
       |          |          |
       |          |          +-> budget exhausted
       |          +------------> extend with new coordinates
       `-----------------------> accepted terminal outcome
```

A retry of one workflow occurrence is not a new scientific coordinate.
Extending the convergence study requests new child workflow occurrences.

The implemented observation associates energy with the existing cubic
mesh/wavefunction-cutoff coordinate but carries no structure or evidence
identity. A new typed correlation wraps those values and the unchanged
assessment without replacing this model.

## Bulk reuse

```text
exact seed structure S0
+ existing grid recipe and policy
+ neutral coupled-cutoff realization
                    |
                    v
separately admitted SCF child occurrences
+ exact request/input/occurrence/evidence and adapter identities
                    |
                    v
typed correlation + existing grid assessment
                    |
                    v
highest tested corner from accepted correlation Q0@S0
```

`Q0@S0` may guide structural relaxation but is not automatically qualified for
the resulting lattice. The planned
[`pw_dft_bulk_qualification`](../pw_dft_bulk_qualification/index.md) composition
owns evidence correlation, fresh confirmation, and any re-relax/reconfirm
feedback; this SCF package owns the reused recipe, assessment, and controller.

## Replay flow

```text
provider-normalized evidence
              |
              v
 typed replay request -> replay actionizer
                              |
                              +-> assessments
                              +-> controller decisions
                              `-> typed replay result
```

Replay performs no provider parsing, filesystem mutation, or calculator
execution.

## Authoritative single-SCF Petri net

```text
start -> registration action -> registered -> submission action -> submitted
                                                        |
                                                        v
                                                     waiting
                                                   /         \
                                             completed      failed
                                                 |
                                          analysis action
                                           /      |       \
                                      success   reject   analysis failure
                                           \      |       /
                                            terminal outcome
```

The migrated local SNAKES `PetriNet` defines this topology, including every
arc, guard, and token expression. The engine-neutral definition inventories
names only; it does not compete with or replace the net. Extraction into a
canonical distributed plan and transition-occurrence lifecycle remains a future
WORKFLOWS concern.

## Dependency direction

```text
repository tools / first-party outward adapters -> public integrations
       |
       v
pw_dft_scf workflows -> protected SCF core
       |
       `-> optional cpn -> pinned snakes

protected SCF core -X-> workflows
production workflows -X-> integrations, adapters, or repository tools
```
