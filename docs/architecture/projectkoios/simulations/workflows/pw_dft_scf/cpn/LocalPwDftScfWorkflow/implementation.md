# `LocalPwDftScfWorkflow` implementation

The class is implemented in `cpn/workflow.py`. `_EVENT_PLACES` is a closed map
from the five supported SCF event classes to boundary places. `_ACTION_PLACES`
fixes deterministic action projection order.

The implementation delegates all mutable-net access to `LocalSnakesRun`.
`status()` observes only approved places, and `outcome()` rejects multiple
terminal tokens. Tests drive registration, submission, waiting, and synthetic
failure without importing example code or executing a calculator.
