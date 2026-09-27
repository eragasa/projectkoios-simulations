from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pytest
from physkit.periodic import DirectLattice3D
from physkit.periodic.unit_cell import (
    Atom,
    AtomicBasis,
    UnitCell,
)
from physkit.units import PhysicalUnit, ScalarQuantity, Unitless, VectorQuantity

from projectkoios.integrations.quantumespresso.pseudopotential import (
    QePseudopotential,
    QePseudopotentialFile,
)
from projectkoios.integrations.quantumespresso.pw.execution import (
    QeSimulationExecutor,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.model import (
    ControlBlock,
    QePwInputFile,
)
from projectkoios.integrations.quantumespresso.pw.simulation import (
    QuantumEspressoSimulation,
)
from projectkoios.simulations.dft.pseudopotential_repository import (
    PseudopotentialRepository,
    PseudopotentialRepositoryEntry,
)
from projectkoios.simulations.dft.pw.settings import CalculationType
from projectkoios.simulations.execution import (
    CalculatorExecutionError,
    ExecutionStatus,
)

pytestmark = pytest.mark.integration


class QeSimulationExecutorTest(unittest.TestCase):
    def test_rejects_execution_without_explicit_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            simulation, repository = _simulation_and_repository(working_directory)

            with self.assertRaisesRegex(PermissionError, "not authorized"):
                QeSimulationExecutor().execute(
                    simulation,
                    repository,
                    Path(sys.executable),
                    working_directory,
                )

            self.assertEqual(tuple(working_directory.iterdir()), ())

    def test_records_missing_repository_artifact_without_starting_qe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            simulation, repository = _simulation_and_repository(working_directory)

            with self.assertRaises(CalculatorExecutionError) as caught:
                QeSimulationExecutor().execute(
                    simulation,
                    repository,
                    Path(sys.executable),
                    working_directory,
                    execution_authorized=True,
                )

            self.assertIs(
                caught.exception.record.status,
                ExecutionStatus.failed_preflight,
            )
            self.assertEqual(
                caught.exception.record.error_type,
                "PseudopotentialNotFoundError",
            )
            self.assertTrue(caught.exception.record_path.is_file())
            self.assertFalse((working_directory / "pw.out").exists())


def _simulation_and_repository(
    working_directory: Path,
) -> tuple[QuantumEspressoSimulation, PseudopotentialRepository]:
    pseudopotential_file = _pseudopotential_file()
    simulation = QuantumEspressoSimulation(
        input_file=QePwInputFile(
            control_block=ControlBlock(
                calculation_type=CalculationType.scf,
                pseudo_dir=".",
            ),
            unit_cell=_unit_cell(),
            groups=(),
        ),
        pseudopotentials=(pseudopotential_file,),
    )
    repository = PseudopotentialRepository(
        entries=(
            PseudopotentialRepositoryEntry(
                pseudopotential_file=pseudopotential_file,
                path=working_directory / "repository" / "Si.upf",
            ),
        )
    )
    return simulation, repository


def _pseudopotential_file() -> QePseudopotentialFile:
    content = b"expected pseudopotential"
    return QePseudopotentialFile(
        pseudopotential=QePseudopotential(
            symbol="Si",
            exchange_correlation="PBE",
            formalism="ONCVPSP",
            relativistic_treatment="scalar-relativistic",
            valence_electrons=4,
            upf_version="2.0.1",
        ),
        filename="Si.upf",
        sha256=hashlib.sha256(content).hexdigest(),
        byte_size=len(content),
    )


def _unit_cell() -> UnitCell:
    return UnitCell(
        direct_lattice=DirectLattice3D(
            a1=np.array([1.0, 0.0, 0.0]),
            a2=np.array([0.0, 1.0, 0.0]),
            a3=np.array([0.0, 0.0, 1.0]),
        ),
        lattice_parameter=ScalarQuantity(5.43, PhysicalUnit("angstrom")),
        atomic_basis=AtomicBasis(
            atoms=(
                Atom(
                    symbol="Si",
                    position_fractional=VectorQuantity(np.zeros(3), Unitless()),
                ),
            )
        ),
    )


if __name__ == "__main__":
    unittest.main()
