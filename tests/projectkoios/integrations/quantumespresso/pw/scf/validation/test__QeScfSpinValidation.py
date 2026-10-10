from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path

import pytest

from projectkoios.integrations.quantumespresso.outputs.pw_stdout import (
    QePwStdoutFile,
    QePwStdoutFileParser,
    QePwStdoutFileResult,
)
from projectkoios.integrations.quantumespresso.pw.execution import (
    QeSimulationExecutor,
)
from projectkoios.integrations.quantumespresso.pw.scf.configuration import (
    QeScfProjectionConfiguration,
    QeScfSpeciesConfiguration,
)
from projectkoios.integrations.quantumespresso.pw.scf.projection import (
    QeScfInputProjector,
)
from projectkoios.simulations.dft.electronic import (
    DftExchangeCorrelationIdentifierScheme,
    DftExchangeCorrelationModel,
    DftOccupationMethod,
    DftOccupationPolicy,
    DftSpinMode,
    DftSpinTreatment,
    PwDftElectronicConvergencePolicy,
)
from projectkoios.simulations.dft.pseudopotential import (
    Pseudopotential,
    PseudopotentialArtifactFormat,
    PseudopotentialFile,
)
from projectkoios.simulations.dft.pseudopotential.library import (
    PseudopotentialLibrary,
)
from projectkoios.simulations.dft.pw.scf.request import PwDftScfRequest
from projectkoios.simulations.dft.pw.scf.specification import PwDftScfSpecification
from projectkoios.simulations.dft.pw.settings import PwDftKPointSamplingPolicy
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation
from projectkoios.simulations.structure.library import (
    StructureLibraryManifestLoader,
    StructureResolution,
)

pytestmark = [pytest.mark.simulation, pytest.mark.validation]

_REPOSITORY_ROOT = Path(__file__).resolve().parents[7]
_STRUCTURE_MANIFEST = (
    _REPOSITORY_ROOT / "examples/workflows/pw_dft_scf/structures/catalog.toml"
)
_PW_EXECUTABLE_SHA256 = (
    "87aa72158e2c103c63fce1deca977dc42ff4ba344519a9662aadb96d33eab910"
)
_PW_EXECUTABLE_BYTE_SIZE = 9_673_048
_RY_TO_EV = 13.605693122994
_ELECTRONIC_TOLERANCE_RY = 1.0e-8

_SI_PSEUDOPOTENTIAL = PseudopotentialFile(
    pseudopotential=Pseudopotential(
        symbol="Si",
        exchange_correlation="PBE",
        formalism="USPP",
        relativistic_treatment="scalar-relativistic",
        valence_electrons=4,
    ),
    artifact_format=PseudopotentialArtifactFormat.UPF,
    artifact_format_version="2.0.1",
    filename="Si.pbe-n-rrkjus_psl.1.0.0.UPF",
    sha256="ae3aefd0811f9499dbc4a72f1f9ae02ef4fc7f3568bf6f559b68668719c69e2b",
    byte_size=1_299_382,
)
_NI_PSEUDOPOTENTIAL = PseudopotentialFile(
    pseudopotential=Pseudopotential(
        symbol="Ni",
        exchange_correlation="PBE",
        formalism="NC",
        relativistic_treatment="scalar-relativistic",
        valence_electrons=18,
    ),
    artifact_format=PseudopotentialArtifactFormat.UPF,
    artifact_format_version="0",
    filename="Ni_PBE_TM_2pj.UPF",
    sha256="7f1c19ab3c45648a5ba4f314cc53335311e0fc04cda8502e27150963b21097ae",
    byte_size=588_165,
)
_EXCHANGE_CORRELATION = DftExchangeCorrelationModel(
    identifier_scheme=DftExchangeCorrelationIdentifierScheme.LIBXC_COMPOSITE,
    identifier="GGA_X_PBE+GGA_C_PBE",
    pseudopotential_compatibility_label="PBE",
)


def test_unpolarized_si_is_the_spin_symmetric_control(tmp_path: Path) -> None:
    structure = _structure("Si.PrimitiveUnitCell")
    request = _request(
        evaluation_id="si-qe-spin-validation",
        simulation_id="Si.QE-7-5.SpinValidation",
        structure=structure,
        pseudopotential=_SI_PSEUDOPOTENTIAL,
        spin=DftSpinTreatment(),
        occupation=DftOccupationPolicy(method=DftOccupationMethod.FIXED),
        mesh=(14, 14, 14),
        wavefunction_cutoff_ry=40.0,
    )
    configuration = QeScfProjectionConfiguration(
        species=(
            QeScfSpeciesConfiguration(
                symbol="Si",
                mass_amu=28.086,
                pseudopotential_filename=_SI_PSEUDOPOTENTIAL.filename,
            ),
        ),
        charge_density_cutoff_ratio=8.0,
        electronic_tolerance_ry=_ELECTRONIC_TOLERANCE_RY,
        prefix="si-spin-control",
    )

    output, input_text = _execute(
        request=request,
        structure=structure,
        configuration=configuration,
        pseudopotential=_SI_PSEUDOPOTENTIAL,
        working_directory=tmp_path,
    )

    # An unpolarized QE calculation has one spin-degenerate channel, so it does
    # not print a separately measured magnetization. This is the exact zero-spin
    # control by model construction, not a noisy near-zero LSDA observation.
    assert "nspin = 2" not in input_text
    assert "starting_magnetization" not in input_text
    assert output.job_completed
    assert output.scf_converged
    assert output.program_version == "7.5"
    assert output.total_magnetization_bohr_magneton_per_cell is None
    assert output.absolute_magnetization_bohr_magneton_per_cell is None


def test_collinear_ferromagnetic_ni_converges_to_nonzero_magnetization(
    tmp_path: Path,
) -> None:
    structure = _structure("materials-project.mp-23.primitive")
    request = _request(
        evaluation_id="ni-qe-spin-validation",
        simulation_id="Ni.MP-23.QE-7-5.SpinValidation",
        structure=structure,
        pseudopotential=_NI_PSEUDOPOTENTIAL,
        # This authored 2 mu_B value is a symmetry-breaking initial condition,
        # not an expected result or acceptance target. QE receives 2/18 because
        # its species parameter is normalized by pseudopotential valence charge.
        spin=DftSpinTreatment(
            mode=DftSpinMode.COLLINEAR,
            initial_site_magnetic_moments_mu_b=(2.0,),
        ),
        occupation=DftOccupationPolicy(
            method=DftOccupationMethod.GAUSSIAN,
            smearing_width_ev=0.02 * _RY_TO_EV,
        ),
        mesh=(12, 12, 12),
        wavefunction_cutoff_ry=100.0,
    )
    configuration = QeScfProjectionConfiguration(
        species=(
            QeScfSpeciesConfiguration(
                symbol="Ni",
                mass_amu=58.6934,
                pseudopotential_filename=_NI_PSEUDOPOTENTIAL.filename,
            ),
        ),
        charge_density_cutoff_ratio=4.0,
        electronic_tolerance_ry=_ELECTRONIC_TOLERANCE_RY,
        prefix="ni-ferromagnetic",
    )

    output, input_text = _execute(
        request=request,
        structure=structure,
        configuration=configuration,
        pseudopotential=_NI_PSEUDOPOTENTIAL,
        working_directory=tmp_path,
    )

    assert "nspin = 2," in input_text
    assert "starting_magnetization(1) = 0.1111111111," in input_text
    assert "occupations = 'smearing'," in input_text
    assert "degauss = 2.0000000000e-02," in input_text
    assert output.job_completed
    assert output.scf_converged
    assert output.program_version == "7.5"
    assert output.total_magnetization_bohr_magneton_per_cell is not None
    assert output.absolute_magnetization_bohr_magneton_per_cell is not None
    assert math.isfinite(output.total_magnetization_bohr_magneton_per_cell)
    assert math.isfinite(output.absolute_magnetization_bohr_magneton_per_cell)
    # The validation accepts only the qualitative ferromagnetic behavior. It
    # does not turn this one unconverged-with-respect-to-method profile into a
    # reference value for elemental Ni.
    assert abs(output.total_magnetization_bohr_magneton_per_cell) > 0.1
    assert output.absolute_magnetization_bohr_magneton_per_cell > 0.1


def _structure(structure_id: str) -> StructureResolution:
    return (
        StructureLibraryManifestLoader(_STRUCTURE_MANIFEST.resolve())
        .load()
        .resolve_unique(structure_id)
    )


def _request(
    *,
    evaluation_id: str,
    simulation_id: str,
    structure: StructureResolution,
    pseudopotential: PseudopotentialFile,
    spin: DftSpinTreatment,
    occupation: DftOccupationPolicy,
    mesh: tuple[int, int, int],
    wavefunction_cutoff_ry: float,
) -> PwDftScfRequest:
    return PwDftScfRequest(
        evaluation_id=evaluation_id,
        specification=PwDftScfSpecification(
            simulation_id=simulation_id,
            simulation=PwDftSimulation(
                structure=structure.record,
                exchange_correlation=_EXCHANGE_CORRELATION,
                spin=spin,
                pseudopotentials=(pseudopotential,),
            ),
            kpoint_sampling=PwDftKPointSamplingPolicy(
                mesh=mesh,
                shift=(0, 0, 0),
                use_spatial_symmetry=True,
                use_time_reversal=True,
            ),
            wavefunction_cutoff_ev=wavefunction_cutoff_ry * _RY_TO_EV,
            occupation=occupation,
            electronic_convergence=PwDftElectronicConvergencePolicy(
                energy_tolerance_ev=_ELECTRONIC_TOLERANCE_RY * _RY_TO_EV,
                maximum_electronic_iterations=200,
            ),
        ),
    )


def _execute(
    *,
    request: PwDftScfRequest,
    structure: StructureResolution,
    configuration: QeScfProjectionConfiguration,
    pseudopotential: PseudopotentialFile,
    working_directory: Path,
) -> tuple[QePwStdoutFileResult, str]:
    executable_value = os.environ.get("PROJECTKOIOS_VALIDATION_QE_PW_EXECUTABLE")
    library_value = os.environ.get("PROJECTKOIOS_VALIDATION_QE_PSEUDOPOTENTIAL_LIBRARY")
    if executable_value is None or library_value is None:
        pytest.skip(
            "QE validation requires explicit executable and pseudopotential-library "
            "environment variables"
        )
    executable = Path(executable_value)
    if (
        not executable.is_absolute()
        or executable.is_symlink()
        or not executable.is_file()
    ):
        raise ValueError("QE validation executable must be an absolute regular file")
    if executable.stat().st_size != _PW_EXECUTABLE_BYTE_SIZE:
        raise ValueError("QE validation executable byte size does not match QE 7.5")
    if _sha256(executable) != _PW_EXECUTABLE_SHA256:
        raise ValueError("QE validation executable SHA-256 does not match QE 7.5")

    projection = QeScfInputProjector(configuration).project(request, structure)
    if tuple(
        requirement.filename for requirement in projection.external_requirements
    ) != (pseudopotential.filename,):
        raise ValueError("QE projection and exact pseudopotential requirement disagree")
    input_file = projection.artifacts[0]

    # Runtime deployment resolution is deliberately in the production executor.
    # The injected library verifies the complete authored requirement and never
    # selects a pseudopotential based only on symbol or filename.
    QeSimulationExecutor().execute(
        prepared_input=projection,
        pseudopotentials=(pseudopotential,),
        pseudopotential_library=PseudopotentialLibrary(Path(library_value)),
        executable=executable,
        working_directory=working_directory,
        output_filename="pw.out",
        timeout_seconds=300.0,
        # The repository-wide pytest gate skips this test unless the same
        # invocation carries explicit operator authorization.
        execution_authorized=True,
    )
    return (
        QePwStdoutFileParser().parse(
            (working_directory / "pw.out").read_bytes(),
            output_file=QePwStdoutFile(relative_path="pw.out"),
        ),
        input_file.content.decode("ascii"),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
