# `projectkoios.simulations`

Calculator-neutral immutable simulation contracts.

- [`calculator`](calculator/index.md) owns structural calculator-integration
  identities.
- [`execution`](execution/index.md) provides fail-loud no-shell process
  execution with durable terminal records.
- [`dft`](dft/index.md) owns density-functional-theory records and
  calculation-mode ports.

Calculator-specific syntax and behavior belong to integrations rather than
this package.

## Extraction boundary

The maintained subtree imports no other `projectkoios.frankensteins` package.
Its simulation records and typed abstract ports depend only on Python's standard
library and PhysKit. Extraction therefore removes only the `frankensteins`
namespace segment and does not require application, adapter, or calculator
implementation code.
