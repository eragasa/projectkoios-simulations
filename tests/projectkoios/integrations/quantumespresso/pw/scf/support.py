from __future__ import annotations

import hashlib
from pathlib import Path

from projectkoios.integrations.quantumespresso.pseudopotential import (
    QePseudopotential,
    QePseudopotentialFile,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator_input import (
    CalculatorExternalInputRequirement,
    CalculatorInputArtifact,
    CalculatorInputRecord,
    CalculatorInputSourceReference,
)
from projectkoios.simulations.dft.pseudopotential_repository import (
    PseudopotentialLibrary,
)

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


def qe_prepared_input() -> CalculatorInputRecord:
    content = (
        b"&CONTROL\n calculation = 'scf'\n pseudo_dir = './'\n outdir = './tmp/'\n/\n"
    )
    pseudopotential = qe_pseudopotential_file()
    return CalculatorInputRecord(
        input_id="Si.QE.PreparedInput",
        schema_version=1,
        source=CalculatorInputSourceReference(
            simulation_id="Si.QE.SCF",
            representation="projectkoios.pw-dft-scf+json",
            schema_version=1,
            byte_size=100,
            sha256="1" * 64,
        ),
        integration_id=CalculatorIntegrationId("quantum-espresso"),
        calculator_name="Quantum ESPRESSO pw.x",
        calculator_version_constraint=">=7.5,<8",
        representation="quantum-espresso-pw-input",
        artifacts=(
            CalculatorInputArtifact(
                role="primary-input",
                filename="pw.in",
                media_type="text/plain; charset=us-ascii",
                content=content,
                byte_size=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
            ),
        ),
        external_requirements=(
            CalculatorExternalInputRequirement(
                role="pseudopotential",
                stable_id=f"Si.{pseudopotential.sha256}",
                filename=pseudopotential.filename,
                format="upf;version=2.0.1",
                byte_size=pseudopotential.byte_size,
                sha256=pseudopotential.sha256,
                provenance="canonical-simulation-specification:" + "1" * 64,
                element_symbol="Si",
            ),
        ),
        mappings=(),
        preparation_operation="projectkoios.qe.pw.scf.prepare",
        preparation_version="1",
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


def qe_library(root: Path) -> PseudopotentialLibrary:
    library_root = root / "repository"
    library_root.mkdir(exist_ok=True)
    return PseudopotentialLibrary(library_root)
