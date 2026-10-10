from __future__ import annotations

import pytest

from projectkoios.simulations.defects import (
    DefectContentReference,
    DefectEnergyCompatibility,
    DefectEnergyEvidence,
    DefectEnergyRole,
    DefectRelaxationEnergyAction,
    DefectRelaxationEnergyRequest,
    DefectSupercellEnergyPair,
    ElementChemicalPotential,
    ElementCountDelta,
    MatchedSizeConvergenceAction,
    MatchedSizeConvergenceRequest,
    NeutralDefectFormationEnergyAction,
    NeutralDefectFormationEnergyRequest,
)


def _reference(stable_id: str, digit: str) -> DefectContentReference:
    return DefectContentReference(
        stable_id=stable_id,
        representation="projectkoios.test+json",
        schema_version=1,
        byte_size=10,
        sha256=digit * 64,
    )


def _energy(
    energy_id: str,
    role: DefectEnergyRole,
    energy_ev: float,
    atom_count: int,
    digit: str,
    qualification_id: str,
) -> DefectEnergyEvidence:
    return DefectEnergyEvidence(
        energy_id=energy_id,
        role=role,
        energy_ev=energy_ev,
        atom_count=atom_count,
        structure=_reference(f"{energy_id}-structure", digit),
        calculation=_reference(f"{energy_id}-calculation", digit),
        method_id="plane-wave-dft",
        model_id="pbe-exact-pseudos-v1",
        qualification_id=qualification_id,
        final_single_point=True,
        completed=True,
        converged=True,
    )


def _compatibility(
    qualification_id: str, evidence: tuple[DefectEnergyEvidence, ...]
) -> DefectEnergyCompatibility:
    return DefectEnergyCompatibility(
        qualification_id=qualification_id,
        evidence_ids=tuple(value.energy_id for value in evidence),
        method_id="plane-wave-dft",
        model_id="pbe-exact-pseudos-v1",
        compatible=True,
        explanation="Exact model and final-SCF requirements match.",
        compared_fields=("method_id", "model_id", "final_single_point"),
        permitted_differences=("structure",),
        limitations=("Synthetic test evidence omits calculator version.",),
    )


def test_neutral_substitution_formation_energy_uses_explicit_reservoirs() -> None:
    qualification_id = "formation-compatible"
    defect = _energy(
        "si-p-64",
        DefectEnergyRole.FULLY_RELAXED_DEFECT,
        -511.0,
        64,
        "1",
        qualification_id,
    )
    pristine = _energy(
        "si-64", DefectEnergyRole.PRISTINE, -512.0, 64, "2", qualification_id
    )
    phosphorus = _energy(
        "p-reference",
        DefectEnergyRole.ELEMENTAL_REFERENCE,
        -10.0,
        2,
        "3",
        qualification_id,
    )
    silicon = _energy(
        "si-reference",
        DefectEnergyRole.ELEMENTAL_REFERENCE,
        -12.0,
        2,
        "4",
        qualification_id,
    )
    evidence = (defect, pristine, phosphorus, silicon)

    result = NeutralDefectFormationEnergyAction().evaluate(
        NeutralDefectFormationEnergyRequest(
            defect=defect,
            pristine=pristine,
            atom_count_deltas=(
                ElementCountDelta("P", 1),
                ElementCountDelta("Si", -1),
            ),
            chemical_potentials=(
                ElementChemicalPotential("P", -5.0, phosphorus),
                ElementChemicalPotential("Si", -6.0, silicon),
            ),
            compatibility=_compatibility(qualification_id, evidence),
        )
    )

    assert result.reservoir_energy_ev == 1.0
    assert result.formation_energy_ev == 0.0


def test_formation_energy_rejects_charged_arithmetic() -> None:
    qualification_id = "charged-rejected"
    defect = _energy(
        "charged-defect", DefectEnergyRole.DEFECT, -10.0, 8, "1", qualification_id
    )
    pristine = _energy(
        "pristine", DefectEnergyRole.PRISTINE, -9.0, 8, "2", qualification_id
    )
    reference = _energy(
        "reference",
        DefectEnergyRole.ELEMENTAL_REFERENCE,
        -1.0,
        1,
        "3",
        qualification_id,
    )

    with pytest.raises(ValueError, match="requires charge_state zero"):
        NeutralDefectFormationEnergyRequest(
            defect=defect,
            pristine=pristine,
            atom_count_deltas=(ElementCountDelta("P", 1),),
            chemical_potentials=(ElementChemicalPotential("P", -1.0, reference),),
            compatibility=_compatibility(
                qualification_id, (defect, pristine, reference)
            ),
            charge_state=1,
        )


def test_relaxation_energy_separates_ionic_and_cell_release() -> None:
    qualification_id = "relaxation-compatible"
    ideal = _energy(
        "ideal", DefectEnergyRole.IDEAL_DEFECT, -100.0, 64, "1", qualification_id
    )
    ion_only = _energy(
        "ion-only",
        DefectEnergyRole.ION_RELAXED_DEFECT,
        -101.5,
        64,
        "2",
        qualification_id,
    )
    fully_relaxed = _energy(
        "fully-relaxed",
        DefectEnergyRole.FULLY_RELAXED_DEFECT,
        -102.0,
        64,
        "3",
        qualification_id,
    )

    result = DefectRelaxationEnergyAction().evaluate(
        DefectRelaxationEnergyRequest(
            ideal=ideal,
            ion_only=ion_only,
            fully_relaxed=fully_relaxed,
            compatibility=_compatibility(
                qualification_id, (ideal, ion_only, fully_relaxed)
            ),
        )
    )

    assert result.ionic_relaxation_energy_ev == 1.5
    assert result.cell_constraint_release_energy_ev == 0.5
    assert result.total_relaxation_energy_ev == 2.0


def test_size_convergence_cancels_matched_chemical_potentials() -> None:
    qualification_id = "size-compatible"
    smaller_defect = _energy(
        "defect-64", DefectEnergyRole.DEFECT, -510.0, 64, "1", qualification_id
    )
    smaller_pristine = _energy(
        "pristine-64", DefectEnergyRole.PRISTINE, -512.0, 64, "2", qualification_id
    )
    larger_defect = _energy(
        "defect-216", DefectEnergyRole.DEFECT, -1725.9, 216, "3", qualification_id
    )
    larger_pristine = _energy(
        "pristine-216",
        DefectEnergyRole.PRISTINE,
        -1728.0,
        216,
        "4",
        qualification_id,
    )
    deltas = (ElementCountDelta("P", 1), ElementCountDelta("Si", -1))
    evidence = (
        smaller_defect,
        smaller_pristine,
        larger_defect,
        larger_pristine,
    )

    result = MatchedSizeConvergenceAction().evaluate(
        MatchedSizeConvergenceRequest(
            smaller=DefectSupercellEnergyPair(
                pristine=smaller_pristine,
                defect=smaller_defect,
                atom_count_deltas=deltas,
            ),
            larger=DefectSupercellEnergyPair(
                pristine=larger_pristine,
                defect=larger_defect,
                atom_count_deltas=deltas,
            ),
            compatibility=_compatibility(qualification_id, evidence),
        )
    )

    assert result.smaller_defect_minus_pristine_ev == 2.0
    assert result.larger_defect_minus_pristine_ev == pytest.approx(2.1)
    assert result.larger_minus_smaller_ev == pytest.approx(0.1)
