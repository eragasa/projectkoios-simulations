# Plane-wave DFT SCF convergence schematics

## Contract flow

Calculator-neutral axis and grid convergence models, policy, assessment, controller outcomes, and qualified cross-backend convergence-test comparison.

```text
caller --> projectkoios.simulations.workflows.pw_dft_scf.convergence --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Existing assessment with outer evidence correlation

```text
existing convergence:
  coordinate + energy per atom + policy
    -> numerical assessment
    -> extend / accept / budget exhausted

additive typed correlation:
  exact structure + request/specification + neutral cutoff realization
    + full sampling policy + projected request/prepared input
    + exact selected occurrence/evidence bytes + adapter mapping per coordinate
    + existing observations and assessment
    -> highest tested corner from accepted correlation Q_i@S_i
```

The typed correlation is a new reusable record; the assessor remains unchanged.
The cross-stage workflow consumes `Q_i@S_i`, performs relaxation, and creates a
fresh correlation around the rerun assessment on the new exact structure.

```text
Q0@S0 -> relaxation -> S1 -> confirmation Q1@S1
                                  |
                   changed Q1 ----+----> re-relax before acceptance
```

No edge grants execution authority. Each coordinate and relaxation is a
separate occurrence admitted outside this package.

## Documented children

`assessment`, `base`, `comparison`, `controller`, `policy`, `replay`

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.convergence` points inward only
to the protected simulation core or to other owner workflow modules. It does
not select a calculator provider, import `projectkoios.integrations` or
`projectkoios.adapters`, discover an executable, grant execution authority, or
own generic Workflow compiler/runtime state. Domain topology or guards
described here remain owner source declarations; canonical CPN places,
transitions, and plans remain compiler-owned.
