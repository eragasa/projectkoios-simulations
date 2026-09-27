# SCF action handlers

`PwDftScfActionHandler` dispatches common actions. `PwDftScfHandlerTask` owns shared task correlation and validation. `MockPwDftScfTask` and `MockPwDftScfActionHandler` provide deterministic synthetic events without another net. `ReplayPwDftScfTask` and `ReplayPwDftScfActionHandler` replay retained calculator evidence through an integration without execution.
