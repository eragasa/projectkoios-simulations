# Workflow definition schematics

## Contract flow

`PwDftScfWorkflowDefinition` inventories the fixed lifecycle names.
`pw_dft_scf_workflow_definition()` constructs it.

```text
authoritative PetriNet --name conformance--> workflow definition inventory
                                                      |
caller ------------------------------------------------+
```

## Documented children

`PwDftScfWorkflowDefinition`

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.workflow.definition` does not
select a calculator provider, import `projectkoios.integrations`, discover an
executable, grant execution authority, or own generic Workflow lifecycle state.
It is not a second topology: arcs, guards, and token expressions remain owned by
the migrated SNAKES `PetriNet` pending WORKFLOWS extraction.
