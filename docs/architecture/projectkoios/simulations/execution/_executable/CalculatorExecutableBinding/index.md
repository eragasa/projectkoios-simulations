# `CalculatorExecutableBinding`

`projectkoios.simulations.execution.CalculatorExecutableBinding` binds one
`CalculatorExecutableIdentity` to an absolute lexical deployment path.
Construction validates the value shape but deliberately performs no filesystem
observation.

Separating immutable identity from mutable deployment state allows
`CalculatorExecutablePreparer` to return a typed read-only observation instead
of hiding filesystem access in value construction.
