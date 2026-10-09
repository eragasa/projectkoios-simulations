# `LocalSnakesRun`

`LocalSnakesRun` is the narrow mutable-engine boundary. It retains one private
SNAKES net and a positive maximum-firing count, accepts typed tokens only at a
caller-selected named place, and exposes deterministic detached token tuples.

`drain_unique()` fires until external input is required. It rejects ambiguous
transition/binding sets and stops with an error if the internal firing bound is
exhausted. It does not expose the underlying net or provide persistence,
leases, retries, or calculator authority.
