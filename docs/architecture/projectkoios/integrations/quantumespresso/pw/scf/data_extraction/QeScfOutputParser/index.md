# `QeScfOutputParser`

`QeScfOutputParser.action(...)` is the pure native-output parsing boundary for
QE SCF stdout and stderr.

Its immutable request supplies:

- exact stdout and stderr bytes;
- safe relative POSIX identifiers for both artifacts; and
- a positive per-stream byte bound.

The request rejects oversized payloads before parsing. The result retains the
exact request and `QePwCapturedStreamData`, including SHA-256, byte size, native
parser results, and source identifiers. Result validation binds those identities
back to the supplied bytes.

The parser has no filesystem or process capability. It does not load paths,
interpret execution success, normalize units, select convergence policy, grant
execution or staging authority, or decide scientific acceptance.

`QeScfDataExtractor` supplies retained bytes to this same actionizer; path-free
callers may supply already-retained bytes directly.
