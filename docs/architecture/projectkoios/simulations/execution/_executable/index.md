# `projectkoios.simulations.execution._executable`

This protected module owns calculator-neutral exact executable identity,
deployment binding, read-only preparation, and typed preparation results.

- [`CalculatorExecutableIdentity`](CalculatorExecutableIdentity/index.md) records
  calculator name, exact version namespace, byte size, and SHA-256.
- [`CalculatorExecutableBinding`](CalculatorExecutableBinding/index.md) binds that
  identity to one absolute lexical path without observing the filesystem.
- [`CalculatorExecutablePreparer`](CalculatorExecutablePreparer/index.md) performs
  read-only, no-process verification and rejects symbolic links.
- [`CalculatorPreparedExecutable`](CalculatorPreparedExecutable/index.md) records
  successful observation without granting execution authority.
- [`CalculatorExecutablePreparationFailure`](CalculatorExecutablePreparationFailure/index.md)
  and its [failure code](CalculatorExecutablePreparationFailureCode/index.md)
  preserve fail-closed mechanical diagnostics.

Preparation does not select a calculator, authorize execution, establish
scientific compatibility, or close a later consumer's mutable-filesystem
boundary. Provider execution owners must stage or reverify exact bytes at their
own effect boundary.
