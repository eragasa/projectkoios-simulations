# `QexsdFinalStructureExtractor`

The constructor requires the maintained parser's immutable `QexsdDocument`;
`extract()` interprets its direct vectors and Cartesian atomic positions as bohr,
solves fractional positions against the source-ordered cell, and returns a PhysKit
`UnitCell`. Raw XML is rejected so mechanical XML parsing remains owned by
`projectkoios.integrations.quantumespresso.qexsd`.
