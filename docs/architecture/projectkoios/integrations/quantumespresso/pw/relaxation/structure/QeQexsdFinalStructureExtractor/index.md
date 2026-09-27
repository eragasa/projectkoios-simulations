# `QeQexsdFinalStructureExtractor`

`extract` consumes the existing parser's immutable QEXSD document. It interprets
QEXSD direct vectors and Cartesian atomic positions as bohr, solves fractional
positions against the source-ordered cell, and returns a PhysKit `UnitCell`.
Raw XML is rejected so XML parsing remains owned by `ksdft2effmass`.
