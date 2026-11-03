# `quantumespresso.qexsd`

This package owns mechanically faithful parsing of explicit Quantum ESPRESSO
QEXSD bytes. `QexsdSource` binds exact bytes to an independently supplied
canonical path, SHA-256 digest, and byte count. `QuantumEspressoXsdDocumentParser`
accepts the observed QEXSD `23.03.10` and `25.05.21` formats under the QES 1.0
namespace and returns an immutable `QexsdDocument`.

The parser preserves source order, native numeric values, declared unit labels,
structural relationships, and source-location labels. It performs no file
discovery, unit conversion, scientific-setting selection, calculation
acceptance, Kohn–Sham semantic construction, or calculator execution.

## Public owners

- `records.QexsdSource`
- `records.QexsdDocument`
- `parsing.QuantumEspressoXsdDocumentParser`

Implementations remain in their defining modules and are not re-exported from
the integration package facade.

## Provenance and limits

The parser and direct tests were transferred from `ksdft2effmass` commit
`aa4098b3d32fe05436a1ba8dab18903a4347b20d`, root tree
`bf89bcd6132e4a5c66a41f26f47fe9ef961421da`. Exact donor paths and Git blob
identities are carried in the installed `provenance.json` resource.

The reduced fixtures verify bounded software behavior only. They do not exhaust
the upstream schemas, establish compatibility with every Quantum ESPRESSO
version, validate calculated material properties, or authorize calculator
execution.
