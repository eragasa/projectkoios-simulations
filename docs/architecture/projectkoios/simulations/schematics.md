# `projectkoios.simulations` schematics

## Dependency direction

```text
                downstream application/domain composition
                         /              |               \
                        v               v                v
          simulations.workflows   integrations/adapters   protected core
                    |                     |
                    +----------+----------+
                               v
                  protected simulations core

owner source declarations -> external compiler binding -> generic Workflow
```

Allowed production dependencies point inward toward the protected core.
Downstream composition may use public workflow and integration contracts, but
production workflow modules do not import provider implementations and
production integration modules do not own workflow policy. The compiler edge is
an external binding direction, not permission for an owner package to import
live Workflow service, kernel, scheduler, or runtime objects.

Forbidden reverse edges are:

```text
protected core -X-> simulations.workflows
protected core -X-> integrations/adapters
simulations.workflows -X-> integrations/adapters
simulations.workflows -X-> application/domain consumers
simulations.workflows -X-> live Workflow runtime objects
downstream Applications/domain consumers -X-> live Workflow runtime objects
```

A future live-runtime integration must cross a separately reviewed external
binding or process boundary. A future stable, runtime-neutral Workflow source
or SDK contract remains a distinct compiler-integration decision.

## Namespace transition

```text
historical source                              current owner

projectkoios.simulation_workflows   ---->     projectkoios.simulations.workflows
```

The transition was one atomic forward move. The old and new production trees
do not coexist. No import alias, re-export, compatibility package, or namespace
shim bridges them.

## Authority flow

```text
scientific specification
        |
        v
pure workflow request -> pure action/composition -> result or execution handoff
                                                     |
                                                     v
                             external runtime/provider authority decision
```

A handoff describes required work; it does not authorize or start a calculator.
Provider-normalized evidence may enter a pure replay action, but provider-native
parsing and execution remain outside the workflow layer.
