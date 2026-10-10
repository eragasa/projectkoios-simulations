from __future__ import annotations

import hashlib
from pathlib import Path

from projectkoios.physkit.periodic.unit_cell import UnitCell, UnitCellJsonCodec
from projectkoios.simulations.dft.electronic import (
    DftChargeState,
    DftExchangeCorrelationIdentifierScheme,
    DftExchangeCorrelationModel,
    DftSpinTreatment,
)
from projectkoios.simulations.dft.pseudopotential import PseudopotentialFile
from projectkoios.simulations.dft.pw.simulation import (
    PwDftSimulation,
    ResolvedPwDftSimulation,
)
from projectkoios.simulations.structure import (
    StructureLibraryManifestLoader,
    StructureRecord,
    StructureRepresentation,
    StructureResolution,
    TransferredStructureProvenance,
)


def silicon_structure_resolution() -> StructureResolution:
    # Reuse the reviewed manifest record so tests exercise the same exact
    # dependency identity that production projectors receive.
    library = StructureLibraryManifestLoader(
        (
            Path(__file__).resolve().parents[5]
            / "examples/workflows/pw_dft_scf/structures/catalog.toml"
        ).resolve()
    ).load()
    return library.resolve_unique("Si.PrimitiveUnitCell")


def unit_cell_structure_resolution(
    unit_cell: UnitCell,
    *,
    structure_id: str = "test.structure.UnitCell",
) -> StructureResolution:
    payload = (
        UnitCellJsonCodec()
        .dumps(
            unit_cell,
            structure_id=structure_id,
        )
        .encode()
    )
    sha256 = hashlib.sha256(payload).hexdigest()
    record = StructureRecord(
        structure_id=structure_id,
        representation=StructureRepresentation.unit_cell,
        schema_version=1,
        sha256=sha256,
        byte_size=len(payload),
        provenance=TransferredStructureProvenance(
            source="test fixture",
            revision="1",
            record_path="fixtures/unit-cell.json",
            source_sha256=sha256,
            result_sha256=sha256,
        ),
    )
    return StructureResolution(
        record=record,
        path=Path("/test/fixtures/unit-cell.json"),
        unit_cell=unit_cell,
    )


def resolved_pw_dft_simulation(
    unit_cell: UnitCell,
    *,
    charge: DftChargeState | None = None,
    spin: DftSpinTreatment | None = None,
    pseudopotentials: tuple[PseudopotentialFile, ...] = (),
) -> ResolvedPwDftSimulation:
    structure = unit_cell_structure_resolution(unit_cell)
    return ResolvedPwDftSimulation(
        simulation=PwDftSimulation(
            structure=structure.record,
            exchange_correlation=pbe_exchange_correlation(),
            charge=DftChargeState() if charge is None else charge,
            spin=DftSpinTreatment() if spin is None else spin,
            pseudopotentials=pseudopotentials,
        ),
        structure=structure,
    )


def pbe_exchange_correlation() -> DftExchangeCorrelationModel:
    return DftExchangeCorrelationModel(
        identifier_scheme=DftExchangeCorrelationIdentifierScheme.LIBXC_COMPOSITE,
        identifier="GGA_X_PBE+GGA_C_PBE",
        pseudopotential_compatibility_label="PBE",
    )
