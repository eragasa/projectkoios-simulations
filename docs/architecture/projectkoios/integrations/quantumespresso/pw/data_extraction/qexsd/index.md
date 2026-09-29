# `QeQexsdData`

Common immutable facade over a document supplied by the maintained
`QuantumEspressoXsdDocumentParser` and the calculator-neutral final structure
interpreted from that document.

The original document record is retained intact. This package does not
reimplement XML parsing, and it does not claim that the upstream document
record models XML sections outside that parser's declared scope.
