# `CalculatorPreparedExecutable`

`projectkoios.simulations.execution.CalculatorPreparedExecutable` records that
one bound executable path was observed as a nonsymlink regular runnable file
whose byte count and SHA-256 matched its declared identity. The observed POSIX
mode bits are retained explicitly.

This is a read-only observation, not an execution grant. A later staging or
process owner must close its own time-of-check/time-of-use boundary because the
filesystem may change after preparation.
