# `projectkoios.simulations.workflows`

## Purpose

`projectkoios.simulations.workflows` is the approved owner-specific composition
layer inside the `projectkoios.simulations` umbrella. It composes protected core
contracts into reusable plane-wave DFT comparison, convergence, assessment,
recipe, replay, relaxation, and workflow-definition capabilities.

The layer is calculator-neutral and provider-independent. It may consume
provider-normalized evidence or return an execution handoff, but it does not
contain calculator-native models, parsers, runners, provider objects, or
execution authority.

At commit `d4323213bffee3551b92f056b8b12f2a193ac15a`, these capabilities still
reside at `projectkoios.simulation_workflows`. This node defines their target
ownership; it does not make the target import path available before the atomic
forward migration.

## Distinction from generic Workflow

The word “workflows” here means simulation-domain capability composition. This
layer owns typed request, action or actionizer, result, and handoff contracts,
plus domain workflow source declarations. A source declaration may state domain
topology and guards, but it does not own canonical CPN objects. A generic
Workflow compiler owns compilation into canonical places, transitions, and
plans; the generic runtime owns occurrence identity, queues, idempotency,
leases, retries, cancellation, reconciliation, delivery, and execution
authority.

The namespace migration itself introduces no dependency on generic Workflow. A
future, separately reviewed compiler integration may use only stable,
runtime-neutral Workflow source or SDK contracts. It must never import service,
kernel, scheduler, or other live runtime implementations.

## Contents after migration

The forward migration will relocate the existing `pw_dft_scf` and
`pw_dft_relaxation` subtrees without semantic restructuring. Their package,
subpackage, and class documentation nodes will be moved only with the code and
will each receive the required `index.md`, `schematics.md`, and
`implementation.md` trio.

See [`schematics.md`](schematics.md) for composition and authority diagrams and
[`implementation.md`](implementation.md) for import, API, migration, and proof
requirements.
