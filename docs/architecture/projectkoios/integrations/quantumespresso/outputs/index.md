# `projectkoios.integrations.quantumespresso.outputs`

Quantum ESPRESSO output support is composed from a `base` module and the
implemented `pw.x` captured-stream modules. Generic result types preserve the
concrete source-file type, and concrete file, parser, and result classes are
closed with `@final`. Unsupported binary, XML, DOS, projected-DOS, auxiliary,
and volumetric parsers are not advertised from placeholder modules. The
package does not re-export implementations.
