# Local SCF colored Petri-net schematics

```text
PwDftScfWorkflowFacade
          ^
          |
LocalPwDftScfWorkflow
          |
          v
build_dft_pw_scf_net -> authoritative snakes.nets.PetriNet
          |
          v
 LocalSnakesRun: typed token insertion, detached snapshots, bounded firing
```

```text
start -> register -> submit -> wait -> complete -> analyze -> success/reject
                              `-> task failure ---------> terminal failure
                                              `-> analysis failure
```

The `PetriNet` above—not the detached name inventory—owns the executable arcs,
guards, and token expressions. External handlers supply typed events. The net
never discovers or invokes a calculator and never treats a test or smoke
invocation as execution authority.
