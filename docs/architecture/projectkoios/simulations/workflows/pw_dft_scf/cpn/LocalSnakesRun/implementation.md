# `LocalSnakesRun` implementation

The class is implemented in `cpn/runtime.py` with slots for `_net` and
`_maximum_firings`. The net is typed as `Any` because SNAKES does not publish
maintained static typing metadata; the public methods retain explicit Python
types.

Construction rejects nonpositive firing bounds. Each drain iteration calculates
currently enabled transitions and their modes once, requires a single pair,
fires it, and records the transition name. Tests exercise deterministic
progression through the typed workflow facade.
