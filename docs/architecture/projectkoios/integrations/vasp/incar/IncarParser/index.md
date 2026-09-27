# `IncarParser`

The public `parse` action converts bounded official generic INCAR syntax into an immutable `IncarFile`. It normalizes tag case and nested-block paths but does not interpret values, apply defaults, or maintain a version-specific tag whitelist.
