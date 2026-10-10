from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator_input import (
    CalculatorInputArtifact,
    CalculatorInputMapping,
    CalculatorInputRecord,
    CalculatorInputSourceReference,
)
from projectkoios.simulations.defects import DefectContentReference, DefectEnergyRole
from projectkoios.simulations.dft.defects import (
    PwDftDefectCompatibilityAction,
    PwDftDefectEnergyBinding,
)
from projectkoios.simulations.dft.pseudopotential import (
    Pseudopotential,
    PseudopotentialArtifactFormat,
    PseudopotentialFile,
)
from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfNativeArtifact,
    PwDftScfObservation,
)
from tests.projectkoios.simulations.dft.pw.scf.support import silicon_scf_request


def _reference(stable_id: str, digit: str) -> DefectContentReference:
    return DefectContentReference(
        stable_id=stable_id,
        representation="test",
        schema_version=1,
        byte_size=10,
        sha256=digit * 64,
    )


def test_dft_binding_requires_exact_input_mappings_and_final_scf() -> None:
    request = silicon_scf_request()
    simulation = replace(
        request.simulation,
        pseudopotentials=(
            PseudopotentialFile(
                pseudopotential=Pseudopotential(
                    symbol="Si",
                    exchange_correlation="PBE",
                    formalism="PAW",
                    relativistic_treatment="scalar-relativistic",
                    valence_electrons=4,
                ),
                artifact_format=PseudopotentialArtifactFormat.UPF,
                artifact_format_version="2.0.1",
                filename="Si.upf",
                sha256="1" * 64,
                byte_size=100,
            ),
        ),
    )
    integration_id = CalculatorIntegrationId("quantum-espresso")
    content = b"input\n"
    calculator_input = CalculatorInputRecord(
        input_id="silicon-input",
        schema_version=1,
        source=CalculatorInputSourceReference(
            simulation_id="silicon-scf",
            representation="test",
            schema_version=1,
            byte_size=10,
            sha256="2" * 64,
        ),
        integration_id=integration_id,
        calculator_name="Quantum ESPRESSO pw.x",
        calculator_version_constraint=">=7,<8",
        representation="qe-pw",
        artifacts=(
            CalculatorInputArtifact(
                role="primary-input",
                filename="pw.in",
                media_type="text/plain",
                content=content,
                byte_size=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
            ),
        ),
        external_requirements=(),
        mappings=(
            CalculatorInputMapping(
                neutral_field="delta_n_electrons",
                neutral_value="0",
                native_fields=("SYSTEM.tot_charge",),
                native_values=("0",),
                effect="constraint",
                qualification="Positive QE charge removes electrons.",
            ),
            CalculatorInputMapping(
                neutral_field="spin",
                neutral_value="unpolarized",
                native_fields=("SYSTEM.nspin",),
                native_values=("1",),
                effect="mode",
                qualification="One QE spin channel represents unpolarized intent.",
            ),
        ),
        preparation_operation="qe.render",
        preparation_version="1",
    )
    observation = PwDftScfObservation(
        total_energy_ev=-10.0,
        atom_count=2,
        electronic_iteration_count=8,
        converged=True,
        completed=True,
        native_artifact=PwDftScfNativeArtifact(
            integration_id=integration_id,
            artifact_id="stdout",
            sha256="3" * 64,
            byte_size=100,
        ),
    )

    binding = PwDftDefectEnergyBinding(
        energy_id="silicon-energy",
        role=DefectEnergyRole.PRISTINE,
        simulation_id="silicon-scf",
        simulation=simulation,
        calculator_input=calculator_input,
        observation=observation,
        structure=_reference("silicon", "4"),
        calculation=_reference("silicon-calculation", "5"),
        model_id="pbe-si-paw-v1",
        qualification_id="silicon-qualified",
    )
    evidence = binding.to_energy_evidence()
    compatibility = PwDftDefectCompatibilityAction().qualify(
        qualification_id="silicon-qualified",
        evidence=(evidence,),
        explanation="Synthetic exact model identity matches.",
    )

    assert evidence.method_id == "plane-wave-dft"
    assert "model_id" in compatibility.compared_fields
    assert compatibility.limitations
    with pytest.raises(ValueError, match="completed converged SCF"):
        replace(binding, observation=replace(observation, converged=False))
