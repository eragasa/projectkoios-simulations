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
SUPERCELL_REPETITIONS = ((2, 2, 2), (3, 3, 3), (4, 4, 4))
SUBSTITUTION_SITE_INDEX = 0
SILICON_BULK_SUPERCELLS = {}
SUBSTITUTION_SITE_ORIGINS = {}
SILICON_PHOSPHORUS_DELTAS = {}
SILICON_BORON_DELTAS = {}
SILICON_PHOSPHORUS_IDEAL_RESULTS = {}
SILICON_BORON_IDEAL_RESULTS = {}

for repetitions in SUPERCELL_REPETITIONS:
    supercell = (
        SuperCellBuilder()
        .action(
            request=SuperCellConstructionRequest(
                source_unit_cell=SILICON_CONVENTIONAL_CELL,
                repetitions=repetitions,
            )
        )
        .supercell
    )
    atom_count = len(supercell.atomic_basis.atoms)
    substitution_site_position = supercell.atomic_basis.atoms[
        SUBSTITUTION_SITE_INDEX
    ].position_fractional
    phosphorus_delta = UnitCellDefectDelta(
        bulk_cell=supercell,
        removals=(SUBSTITUTION_SITE_INDEX,),
        additions=(Atom(symbol="P", position_fractional=substitution_site_position),),
        charge_state=0,
    )
    boron_delta = UnitCellDefectDelta(
        bulk_cell=supercell,
        removals=(SUBSTITUTION_SITE_INDEX,),
        additions=(Atom(symbol="B", position_fractional=substitution_site_position),),
        charge_state=0,
    )

    SILICON_BULK_SUPERCELLS[atom_count] = supercell
    SUBSTITUTION_SITE_ORIGINS[atom_count] = supercell.site_origins[
        SUBSTITUTION_SITE_INDEX
    ]
    SILICON_PHOSPHORUS_DELTAS[atom_count] = phosphorus_delta
    SILICON_BORON_DELTAS[atom_count] = boron_delta
    SILICON_PHOSPHORUS_IDEAL_RESULTS[atom_count] = (
        UnitCellDefectDeltaApplicator().action(request=phosphorus_delta)
    )
    SILICON_BORON_IDEAL_RESULTS[atom_count] = UnitCellDefectDeltaApplicator().action(
        request=boron_delta
    )
