# `projectkoios.simulations.dft`

Calculator-neutral density-functional-theory records.

- [`pseudopotential`](pseudopotential/index.md) owns pseudopotential metadata
  and file identities.
- [`pseudopotential_repository`](pseudopotential_repository/index.md) resolves
  exact local artifacts.
- [`pw`](pw/index.md) owns plane-wave DFT simulations, settings, and
  calculation-mode contracts.

The package does not select a calculator, pseudopotential family, scientific
model, or convergence setting.
