# `projectkoios.simulations.dft`

Calculator-neutral density-functional-theory records.

- [`pseudopotential`](pseudopotential/index.md) owns pseudopotential metadata,
  exact file identities, and machine-local byte resolution.
- [`pw`](pw/index.md) owns plane-wave DFT simulations, settings, and
  calculation-mode contracts.

The package does not select a calculator, pseudopotential family, scientific
model, or convergence setting.
