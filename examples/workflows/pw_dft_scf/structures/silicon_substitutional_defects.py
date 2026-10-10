"""Declare exact neutral ideal Si:P and Si:B substitutional defect cells."""

from pathlib import Path

from projectkoios.physkit.periodic.unit_cell import Atom
from projectkoios.simulations.structure import (
    StructureLibraryManifestLoader,
    SuperCellBuilder,
    SuperCellConstructionRequest,
    UnitCellDefectDelta,
    UnitCellDefectDeltaApplicator,
)

STRUCTURE_LIBRARY = StructureLibraryManifestLoader(
    manifest_path=Path(__file__).with_name("catalog.toml").resolve()
).load()
SILICON_CONVENTIONAL_RECORD = STRUCTURE_LIBRARY.require_unique(
    "Si.ConventionalUnitCell"
)
SILICON_CONVENTIONAL_CELL = STRUCTURE_LIBRARY.resolve(
    SILICON_CONVENTIONAL_RECORD
).unit_cell
SILICON_BULK_SUPERCELL = (
    SuperCellBuilder()
    .action(
        request=SuperCellConstructionRequest(
            source_unit_cell=SILICON_CONVENTIONAL_CELL,
            repetitions=(2, 2, 2),
        )
    )
    .supercell
)

SUBSTITUTION_SITE_INDEX = 0
SUBSTITUTION_SITE_ORIGIN = SILICON_BULK_SUPERCELL.site_origins[SUBSTITUTION_SITE_INDEX]
SUBSTITUTION_SITE_POSITION = SILICON_BULK_SUPERCELL.atomic_basis.atoms[
    SUBSTITUTION_SITE_INDEX
].position_fractional

SILICON_PHOSPHORUS_DELTA = UnitCellDefectDelta(
    bulk_cell=SILICON_BULK_SUPERCELL,
    removals=(SUBSTITUTION_SITE_INDEX,),
    additions=(Atom(symbol="P", position_fractional=SUBSTITUTION_SITE_POSITION),),
    charge_state=0,
)
SILICON_BORON_DELTA = UnitCellDefectDelta(
    bulk_cell=SILICON_BULK_SUPERCELL,
    removals=(SUBSTITUTION_SITE_INDEX,),
    additions=(Atom(symbol="B", position_fractional=SUBSTITUTION_SITE_POSITION),),
    charge_state=0,
)

SILICON_PHOSPHORUS_IDEAL_RESULT = UnitCellDefectDeltaApplicator().action(
    request=SILICON_PHOSPHORUS_DELTA
)
SILICON_BORON_IDEAL_RESULT = UnitCellDefectDeltaApplicator().action(
    request=SILICON_BORON_DELTA
)
