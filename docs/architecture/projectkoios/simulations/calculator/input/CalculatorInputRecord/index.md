# `CalculatorInputRecord`

`projectkoios.simulations.calculator.input.CalculatorInputRecord` is the complete
immutable prepared-input record. It correlates the source simulation,
integration identity, native representation, exact rendered artifacts, exact
external requirements, mapping observations, and preparation provenance.

Its canonical JSON identity excludes embedded artifact bytes while retaining
every artifact byte count and SHA-256. The record grants no calculator
execution authority.
