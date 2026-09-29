from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from projectkoios.integrations.quantumespresso.pseudopotential import (
    QePseudopotential,
    QePseudopotentialFile,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.model import (
    ControlBlock,
    QePwInputFile,
)
from projectkoios.integrations.quantumespresso.pw.simulation import (
    QuantumEspressoSimulation,
)
from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.physkit.periodic.unit_cell import (
    Atom,
    AtomicBasis,
    UnitCell,
)
from projectkoios.physkit.units import (
    PhysicalUnit,
    ScalarQuantity,
    Unitless,
    VectorQuantity,
)
from projectkoios.simulations.dft.pseudopotential_repository import (
    PseudopotentialRepository,
    PseudopotentialRepositoryEntry,
)
from projectkoios.simulations.dft.pw.settings import CalculationType

EXPECTED_PROGRAM_VERSION = "7.5"
EXPECTED_ATOM_COUNT = 2
EXPECTED_IRREDUCIBLE_KPOINT_COUNT = 29
EXPECTED_WAVEFUNCTION_CUTOFF_RY = 30.0
EXPECTED_ELECTRONIC_ITERATION_COUNT = 5
EXPECTED_TOTAL_ENERGY_RY = -22.83930406

# Independent retained-output fixture: do not generate this text from expectations.
QE_PW_OUTPUT = """Program PWSCF v.7.5 starts on 1Jan2026
     number of atoms/cell      =            2
     number of k points=    29
     kinetic-energy cutoff     =      30.0000  Ry
     iteration #  1
     iteration #  2
     iteration #  3
     iteration #  4
     iteration #  5
     convergence has been achieved in 5 iterations
!    total energy              =     -22.83930406 Ry
JOB DONE.
"""
QE_STDERR = """Note: The following floating-point exceptions are signalling:
 IEEE_INVALID_FLAG IEEE_DIVIDE_BY_ZERO IEEE_OVERFLOW_FLAG IEEE_UNDERFLOW_FLAG
"""
QE_SUCCESSFUL_EXECUTION_RECORD = {
    "schema_version": 1,
    "status": "succeeded",
    "returncode": 0,
    "stdout_filename": "pw.out",
    "stderr_filename": "pw.err",
}


def qe_simulation() -> QuantumEspressoSimulation:
    return QuantumEspressoSimulation(
        input_file=QePwInputFile(
            control_block=ControlBlock(
                calculation_type=CalculationType.scf,
                pseudo_dir=".",
            ),
            unit_cell=UnitCell(
                direct_lattice=DirectLattice3D(
                    a1=np.array([1.0, 0.0, 0.0]),
                    a2=np.array([0.0, 1.0, 0.0]),
                    a3=np.array([0.0, 0.0, 1.0]),
                ),
                lattice_parameter=ScalarQuantity(
                    magnitude=5.43,
                    unit=PhysicalUnit(expression="angstrom"),
                ),
                atomic_basis=AtomicBasis(
                    atoms=(
                        Atom(
                            symbol="Si",
                            position_fractional=VectorQuantity(
                                magnitude=np.zeros(3),
                                unit=Unitless(),
                            ),
                        ),
                    )
                ),
            ),
            groups=(),
        ),
        pseudopotentials=(qe_pseudopotential_file(),),
    )


def qe_pseudopotential_file() -> QePseudopotentialFile:
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


def qe_repository(root: Path) -> PseudopotentialRepository:
    pseudo = qe_pseudopotential_file()
    return PseudopotentialRepository(
        entries=(
            PseudopotentialRepositoryEntry(
                pseudopotential_file=pseudo,
                path=root / "repository" / pseudo.filename,
            ),
        )
    )
