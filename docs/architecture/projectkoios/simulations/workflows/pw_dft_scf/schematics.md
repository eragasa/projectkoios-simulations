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

## Single-SCF lifecycle source

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

The owner declaration names this topology and its domain guards. The optional
local SNAKES net realizes it in process; canonical distributed CPN plans and
transition-occurrence lifecycle remain future WORKFLOWS concerns.

## Dependency direction

```text
repository tools -> public integrations
       |
       v
pw_dft_scf workflows -> protected SCF core
       |
       `-> optional cpn -> pinned snakes

protected SCF core -X-> workflows
production workflows -X-> integrations or repository tools
```
