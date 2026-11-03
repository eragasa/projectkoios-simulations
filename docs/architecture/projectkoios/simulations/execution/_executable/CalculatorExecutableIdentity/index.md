# `CalculatorExecutableIdentity`

`projectkoios.simulations.execution.CalculatorExecutableIdentity` is the
calculator-neutral immutable identity of one exact executable. It records the
calculator name, exact declared version, positive byte count, and lowercase
SHA-256 digest.

The record identifies bytes only. It does not locate an executable, infer the
version by process invocation, establish provider compatibility, grant
execution authority, or validate scientific behavior.
