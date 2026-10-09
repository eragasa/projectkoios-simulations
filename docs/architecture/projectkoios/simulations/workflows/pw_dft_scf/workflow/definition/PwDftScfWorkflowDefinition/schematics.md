# PwDftScfWorkflowDefinition schematics

## Contract flow

Fields: `name`, `places`, `transitions`.

```text
authoritative PetriNet --name conformance--> PwDftScfWorkflowDefinition
                                                      |
caller ------------------------------------------------+
```

## Documented children

No child documentation nodes; the index defines the complete local role.

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.workflow.definition` does not
select a calculator provider, import `projectkoios.integrations`, discover an
executable, grant execution authority, or own generic Workflow lifecycle state.
The migrated SNAKES `PetriNet` remains authoritative for executable topology
until WORKFLOWS extraction.
