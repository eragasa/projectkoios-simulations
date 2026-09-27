# `projectkoios.integrations.vasp.incar`

See the [INCAR I/O architecture schematic](architecture.md) for the parsing, representation, and rendering boundaries.

The format authority is the official VASP [`INCAR`](https://vasp.at/wiki/INCAR) page. `INCAR_DOCUMENTATION_URL` retains that URL. The evolving tag authority is the supplied [`INCAR tag` category](https://vasp.at/wiki/Category:INCAR_tag), retained as `INCAR_TAG_DOCUMENTATION_URL`.

The category currently contains hundreds of paginated, version-dependent tags. Consequently this module does not freeze a tag whitelist. `IncarAssignment` retains a normalized syntactic tag and lexical value, while `IncarFile` preserves assignment order. `IncarParser` performs bounded parsing through `parse`; `IncarWriter` performs deterministic direct-tag rendering through `render`. `IncarSyntaxError` identifies malformed input.

The parser supports the official generic syntax: `TAG = value`, semicolon-separated statements, `#` and `!` comments, line-ending backslash continuation, quoted multiline values, direct nested tags, and curly-brace nested-tag blocks. Curly-brace blocks are normalized to direct slash-separated tags when rendered. It requires plain ASCII, Unix line endings, and no tabs.

Syntax handling does not determine whether a tag is admitted by a particular VASP version or build, whether combinations are compatible, or whether settings are scientifically appropriate. VASP's OUTCAR interpretation remains the calculator-side check of applied settings.
