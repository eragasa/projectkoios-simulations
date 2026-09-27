# `QeRelaxationCalculationRunRequest`

`QeRelaxationCalculationRunRequest` exposes `configuration_path`,
`output_directory`, `execute`, `structure_override`, `executable`,
`pseudopotential`, and `timeout_seconds`.

`execute=False` forbids execution resources and remains render-only.
`execute=True` explicitly authorizes calculator execution and requires both
exact resource paths. Constructing either request does not itself perform a
calculator effect; `QeRelaxationCalculationRunner.run` performs the requested
action.
