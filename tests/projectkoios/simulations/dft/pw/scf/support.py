from __future__ import annotations

from projectkoios.simulations.dft.electronic import (
    DftOccupationMethod,
    DftOccupationPolicy,
    PwDftElectronicConvergencePolicy,
)
from projectkoios.simulations.dft.pseudopotential import (
    Pseudopotential,
    PseudopotentialArtifactFormat,
    PseudopotentialFile,
)
from projectkoios.simulations.dft.pw.scf.request import PwDftScfRequest
from projectkoios.simulations.dft.pw.scf.specification import PwDftScfSpecification
from projectkoios.simulations.dft.pw.settings import PwDftKPointSamplingPolicy
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation
from tests.projectkoios.simulations.dft.pw.support import (
    pbe_exchange_correlation,
    silicon_structure_resolution,
)


def silicon_scf_request() -> PwDftScfRequest:
    structure = silicon_structure_resolution()
    return PwDftScfRequest(
        evaluation_id="silicon-scf",
        specification=PwDftScfSpecification(
            simulation_id="Si.PrimitiveUnitCell.QE.SCF",
            simulation=PwDftSimulation(
                structure=structure.record,
                exchange_correlation=pbe_exchange_correlation(),
                pseudopotentials=(
                    PseudopotentialFile(
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
                        sha256="1" * 64,
                        byte_size=100,
                    ),
                ),
            ),
            kpoint_sampling=PwDftKPointSamplingPolicy(
                mesh=(8, 8, 8),
                shift=(0, 0, 0),
                use_spatial_symmetry=True,
                use_time_reversal=True,
            ),
            wavefunction_cutoff_ev=400.0,
            occupation=DftOccupationPolicy(method=DftOccupationMethod.FIXED),
            # 1.0e-6 Ry converted to eV preserves the maintained QE fixture.
            electronic_convergence=PwDftElectronicConvergencePolicy(
                energy_tolerance_ev=1.3605693122994e-5,
                maximum_electronic_iterations=100,
            ),
        ),
    )
