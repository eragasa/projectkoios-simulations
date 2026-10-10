from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from projectkoios.simulations.workflows.pw_dft_scf.workflow.definition import (
    pw_dft_scf_workflow_definition,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CPN_IMPLEMENTATION = (
    REPOSITORY_ROOT
    / "docs"
    / "architecture/projectkoios/simulations/workflows/pw_dft_scf/cpn"
    / "implementation.md"
)
PSEUDOPOTENTIAL_LIBRARY = (
    REPOSITORY_ROOT
    / "docs/projectkoios/simulations/dft/pseudopotential/library"
    / "PseudopotentialLibrary/index.md"
)
LOCAL_EXECUTION = REPOSITORY_ROOT / "docs/local-execution.md"
STRUCTURE_LIBRARY_ARCHITECTURE = (
    REPOSITORY_ROOT / "docs/architecture/projectkoios/simulations/structure/library"
)
STRUCTURE_LIBRARY = STRUCTURE_LIBRARY_ARCHITECTURE / "index.md"
STRUCTURE_DEFECT = (
    REPOSITORY_ROOT
    / "docs/architecture/projectkoios/simulations/structure/defect/index.md"
)
MATERIALS_PROJECT_ARCHITECTURE = (
    REPOSITORY_ROOT / "docs/architecture/projectkoios/integrations/materials_project"
)
MATERIALS_PROJECT = MATERIALS_PROJECT_ARCHITECTURE / "index.md"
SIMULATION_LIBRARY_ARCHITECTURE = (
    REPOSITORY_ROOT / "docs/architecture/projectkoios/simulations/library"
)
SIMULATION_EVIDENCE_ARCHITECTURE = (
    REPOSITORY_ROOT / "docs/architecture/projectkoios/simulations/evidence"
)
CALCULATOR_INPUT_ARCHITECTURE = (
    REPOSITORY_ROOT / "docs/architecture/projectkoios/simulations/calculator_input"
)
DEFECTS_ARCHITECTURE = (
    REPOSITORY_ROOT / "docs/architecture/projectkoios/simulations/defects"
)
DFT_DEFECTS_ARCHITECTURE = (
    REPOSITORY_ROOT / "docs/architecture/projectkoios/simulations/dft/defects"
)
PW_DFT_RELAXATION_ARCHITECTURE = (
    REPOSITORY_ROOT / "docs/architecture/projectkoios/simulations/dft/pw/relaxation"
)
PW_DFT_DEFECT_WORKFLOW_ARCHITECTURE = (
    REPOSITORY_ROOT
    / "docs/architecture/projectkoios/simulations/workflows"
    / "pw_dft_defect_formation"
)
UNIMPLEMENTED_TARGET_ARCHITECTURE_TRIOS = (PW_DFT_DEFECT_WORKFLOW_ARCHITECTURE,)
INITIAL_IMPLEMENTATION_ARCHITECTURE_TRIOS = (
    SIMULATION_LIBRARY_ARCHITECTURE,
    SIMULATION_EVIDENCE_ARCHITECTURE,
    CALCULATOR_INPUT_ARCHITECTURE,
    DEFECTS_ARCHITECTURE,
    DFT_DEFECTS_ARCHITECTURE,
)
MIXED_STATUS_ARCHITECTURE_TRIOS = (
    STRUCTURE_LIBRARY_ARCHITECTURE,
    PW_DFT_RELAXATION_ARCHITECTURE,
    MATERIALS_PROJECT_ARCHITECTURE,
)
ARCHITECTURE_TRIOS = (
    UNIMPLEMENTED_TARGET_ARCHITECTURE_TRIOS
    + INITIAL_IMPLEMENTATION_ARCHITECTURE_TRIOS
    + MIXED_STATUS_ARCHITECTURE_TRIOS
)
SCIENTIFIC_NUMERIC_ARCHITECTURE_NODES = (
    DEFECTS_ARCHITECTURE,
    DFT_DEFECTS_ARCHITECTURE,
    PW_DFT_DEFECT_WORKFLOW_ARCHITECTURE,
    STRUCTURE_LIBRARY_ARCHITECTURE,
    PW_DFT_RELAXATION_ARCHITECTURE,
    MATERIALS_PROJECT_ARCHITECTURE,
)
_LINK = re.compile(r"\[[^]]*\]\(([^)]+)\)")


def test_revised_navigation_documents_have_no_broken_relative_links() -> None:
    documents = (
        REPOSITORY_ROOT / "README.md",
        REPOSITORY_ROOT / "docs/architecture/projectkoios/simulations/index.md",
        REPOSITORY_ROOT
        / "docs/architecture/projectkoios/simulations/workflows/index.md",
        REPOSITORY_ROOT / "examples/README.md",
        REPOSITORY_ROOT / "examples/projectkoios/README.md",
        REPOSITORY_ROOT / "examples/projectkoios/simulations/README.md",
        REPOSITORY_ROOT
        / "docs"
        / "architecture/projectkoios/simulations/workflows/pw_dft_scf/cpn/index.md",
        REPOSITORY_ROOT / "docs/projectkoios/simulations/dft/pseudopotential/index.md",
        REPOSITORY_ROOT
        / "docs/projectkoios/simulations/dft/pseudopotential/library/index.md",
        REPOSITORY_ROOT
        / "docs/architecture/projectkoios/simulations/structure/index.md",
        STRUCTURE_LIBRARY,
        STRUCTURE_DEFECT,
        REPOSITORY_ROOT / "docs/projectkoios/simulations/structure/index.md",
        REPOSITORY_ROOT / "examples/workflows/pw_dft_scf/README.md",
        MATERIALS_PROJECT,
        *(
            document
            for directory in ARCHITECTURE_TRIOS
            for document in directory.glob("*.md")
        ),
    )

    broken: list[tuple[str, str]] = []
    for document in documents:
        for raw_target in _LINK.findall(document.read_text(encoding="utf-8")):
            parsed = urlparse(raw_target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (document.parent / unquote(parsed.path)).resolve()
            if not target.exists():
                broken.append((str(document.relative_to(REPOSITORY_ROOT)), raw_target))

    assert broken == []


def test_cpn_reference_names_every_authoritative_place_and_transition() -> None:
    definition = pw_dft_scf_workflow_definition()
    documentation = CPN_IMPLEMENTATION.read_text(encoding="utf-8")

    assert "twelve typed places" in documentation
    assert "eight transitions" in documentation
    for name in (*definition.places, *definition.transitions):
        assert f"`{name}`" in documentation


def test_pseudopotential_library_reference_covers_api_and_failures() -> None:
    documentation = PSEUDOPOTENTIAL_LIBRARY.read_text(encoding="utf-8")

    for required_section in (
        "## Construction contract",
        "## `resolve(required)`",
        "### Resolution failures",
        "## Example",
    ):
        assert required_section in documentation
    for error_name in (
        "PseudopotentialNotFoundError",
        "PseudopotentialIntegrityError",
        "TypeError",
        "ValueError",
    ):
        assert error_name in documentation


def test_structure_library_and_defect_contracts_are_documented() -> None:
    library = " ".join(STRUCTURE_LIBRARY.read_text(encoding="utf-8").split())
    defect = " ".join(STRUCTURE_DEFECT.read_text(encoding="utf-8").split())

    for required in (
        "StructureRecord",
        "StructureRepresentation",
        "TransferredStructureProvenance",
        "DerivedStructureProvenance",
        "ObservedStructureProvenance",
        "unit-cell",
        "byte size",
        "SHA-256",
        "PrimitiveUnitCell",
        "ConventionalUnitCell",
        "StructureConflictError",
        "does not discover, authorize, or run a calculator",
    ):
        assert required in library
    for required in (
        "UnitCellDefectDelta",
        "original `bulk_cell.atomic_basis.atoms` tuple",
        "simultaneously",
        "base `UnitCell`",
        "charge_state",
        "delta_n_electrons",
        "charge_state == -delta_n_electrons",
        "(2, 2, 2)",
        "Si:P",
        "Si:B",
        "relaxed defect structure",
        "does not authorize calculator execution",
    ):
        assert required in defect


def test_architecture_trios_are_substantive_and_status_qualified() -> None:
    required_names = {"index.md", "implementation.md", "schematics.md"}
    optional_names = {"scientific.md", "numeric.md"}

    for directory in ARCHITECTURE_TRIOS:
        documents = {path.name: path for path in directory.glob("*.md")}

        assert required_names <= set(documents)
        assert set(documents) <= required_names | optional_names
        for document in documents.values():
            text = document.read_text(encoding="utf-8")
            assert text.startswith("# ")
            assert "\n## " in text
            assert len(text) >= 1_000

    for directory in UNIMPLEMENTED_TARGET_ARCHITECTURE_TRIOS:
        index = " ".join((directory / "index.md").read_text(encoding="utf-8").split())
        assert "## Status" in index
        assert "do not yet exist" in index

    for directory in INITIAL_IMPLEMENTATION_ARCHITECTURE_TRIOS:
        index = " ".join((directory / "index.md").read_text(encoding="utf-8").split())
        assert "## Status" in index
        assert "initial protected-core implementation" in index.lower()

    for directory in SCIENTIFIC_NUMERIC_ARCHITECTURE_NODES:
        assert {"scientific.md", "numeric.md"} <= {
            path.name for path in directory.glob("*.md")
        }


def test_target_architecture_preserves_identity_and_authority_boundaries() -> None:
    library = " ".join(
        (SIMULATION_LIBRARY_ARCHITECTURE / "index.md")
        .read_text(encoding="utf-8")
        .split()
    )
    library_scientific = " ".join(
        (SIMULATION_LIBRARY_ARCHITECTURE / "scientific.md")
        .read_text(encoding="utf-8")
        .split()
    )
    evidence = " ".join(
        (SIMULATION_EVIDENCE_ARCHITECTURE / "index.md")
        .read_text(encoding="utf-8")
        .split()
    )
    energetics = " ".join(
        (DEFECTS_ARCHITECTURE / "index.md").read_text(encoding="utf-8").split()
    )
    dft_binding = " ".join(
        (DFT_DEFECTS_ARCHITECTURE / "index.md").read_text(encoding="utf-8").split()
    )
    workflow = " ".join(
        (PW_DFT_DEFECT_WORKFLOW_ARCHITECTURE / "index.md")
        .read_text(encoding="utf-8")
        .split()
    )
    workflow_scientific = " ".join(
        (PW_DFT_DEFECT_WORKFLOW_ARCHITECTURE / "scientific.md")
        .read_text(encoding="utf-8")
        .split()
    )

    for required in (
        "SimulationRecord",
        "evaluation_id",
        "not an exact identity",
        "compatibility facades are not permitted",
        "delta_n_electrons",
        "defect.charge_state == -simulation.delta_n_electrons",
        "neutral Si:P records require a spin-polarized doublet",
    ):
        assert required in library
    for required in (
        "StructureRecord",
        "PseudopotentialFile",
        "upf",
        "vasp-potcar",
        "noncollinear",
        "spin-orbit-coupled",
        "from-exact-starting-structure",
        "selected-components",
        "CalculatorInputRecord",
        "no mixed old/new request interval",
    ):
        assert required in library_scientific
    for required in (
        "SimulationEvidenceRecord",
        "does not own",
        "calculator credentials",
        "scientific acceptance",
    ):
        assert required in evidence
    for required in (
        "projectkoios.simulations.defects",
        "independently of whether those energies come from plane-wave DFT",
        "UnitCellDefectDelta",
        "E_f(X_Si^0)",
        "rejects nonzero charge",
        "ideal defect at the host-supercell lattice parameters",
        "ion-only relaxed defect",
        "fully relaxed defect",
        "E_strain = E_final(ion-only relaxed)",
    ):
        assert required in energetics
    for required in (
        "projectkoios.simulations.dft.defects",
        "projectkoios.simulations.defects",
        "charge_state == -delta_n_electrons",
        "neutral Si:P and Si:B workflow requires collinear spin-polarized doublets",
        "does not duplicate the generic formation-energy",
    ):
        assert required in dft_binding
    for required in (
        "64-, 216-, and 512-atom",
        "non-authorizing",
        "does not displace the current SCF Petri-net authority",
        "fixed-host ion relaxation",
        "lowest compatible converged observed basin",
        "Every neutral Si:P and Si:B stage is explicitly spin-polarized as a doublet",
    ):
        assert required in workflow
    for required in (
        "Materials Project",
        "charge_state == -delta_n_electrons",
        "Neutral Si:P is a spin-polarized doublet",
        "Neutral substitutional Si:B likewise has an odd valence-electron count",
        "delta_n_electrons`, which remains zero",
    ):
        assert required in workflow_scientific


def test_scientific_and_numeric_documents_qualify_claims_and_citations() -> None:
    for directory in SCIENTIFIC_NUMERIC_ARCHITECTURE_NODES:
        for name in ("scientific.md", "numeric.md"):
            text = (directory / name).read_text(encoding="utf-8")
            assert "does not" in text.lower()
            if "## References" in text:
                assert "https://doi.org/" in text

    for directory, names in (
        (DEFECTS_ARCHITECTURE, ("scientific.md", "numeric.md")),
        (DFT_DEFECTS_ARCHITECTURE, ("scientific.md", "numeric.md")),
        (PW_DFT_DEFECT_WORKFLOW_ARCHITECTURE, ("scientific.md", "numeric.md")),
        (PW_DFT_RELAXATION_ARCHITECTURE, ("scientific.md",)),
        (MATERIALS_PROJECT_ARCHITECTURE, ("scientific.md",)),
    ):
        for name in names:
            assert "## References" in (directory / name).read_text(encoding="utf-8")


def test_new_prerequisite_architecture_is_explicit() -> None:
    calculator_input = " ".join(
        (CALCULATOR_INPUT_ARCHITECTURE / "index.md").read_text(encoding="utf-8").split()
    )
    structure = " ".join(
        (STRUCTURE_LIBRARY_ARCHITECTURE / "implementation.md")
        .read_text(encoding="utf-8")
        .split()
    )
    relaxation = " ".join(
        (PW_DFT_RELAXATION_ARCHITECTURE / "index.md")
        .read_text(encoding="utf-8")
        .split()
    )
    materials_project = " ".join(
        (MATERIALS_PROJECT_ARCHITECTURE / "index.md")
        .read_text(encoding="utf-8")
        .split()
    )

    for required in (
        "CalculatorInputRecord",
        "Which exact calculator input files",
        "does not authorize execution",
        "delta_n_electrons",
        "spin-polarized doublet",
    ):
        assert required in calculator_input
    for required in (
        'StructureRepresentation.unit_cell = "unit-cell"',
        "TransferredStructureProvenance",
        "DerivedStructureProvenance",
        "ObservedStructureProvenance",
        "PhysKit `UnitCellJsonCodec` extension",
        "structure package imports neither owning package",
    ):
        assert required in structure
    for required in (
        "PwDftRelaxationObservation",
        "PwDftRelaxationResult",
        "PwDftRelaxedStructurePublisher",
        "canonical observation bytes",
        "final base `UnitCell`",
        "cell-relaxation mode",
        "does not select which mode",
    ):
        assert required in relaxation
    for required in (
        "MaterialsProjectQuerySnapshot",
        "canonical candidate set",
        "candidate-response digest",
        "not a claim that a later live query will be reproducible",
    ):
        assert required in materials_project


def test_provider_defect_input_and_output_requirements_are_documented() -> None:
    qe_scf_input = " ".join(
        (
            REPOSITORY_ROOT
            / "docs/architecture/projectkoios/integrations/quantumespresso"
            / "pw/scf/projection/index.md"
        )
        .read_text(encoding="utf-8")
        .split()
    )
    qe_relaxation_input = " ".join(
        (
            REPOSITORY_ROOT
            / "docs/architecture/projectkoios/integrations/quantumespresso"
            / "pw/relaxation/projection/index.md"
        )
        .read_text(encoding="utf-8")
        .split()
    )
    vasp_scf_input = " ".join(
        (
            REPOSITORY_ROOT
            / "docs/architecture/projectkoios/integrations/vasp"
            / "pw_dft_scf/projection/index.md"
        )
        .read_text(encoding="utf-8")
        .split()
    )

    for documentation in (qe_scf_input, qe_relaxation_input, vasp_scf_input):
        assert "CalculatorInputRecord" in documentation
        assert "delta_n_electrons" in documentation
        assert "spin" in documentation
        assert "does not authorize" in documentation
    assert "positive-charge convention" in qe_scf_input
    assert "cell-relaxation mode" in qe_relaxation_input
    assert "neutral valence electron count" in vasp_scf_input
    assert "VASP relaxation input translator" in vasp_scf_input


def test_materials_project_hull_boundary_is_documented() -> None:
    documentation = " ".join(MATERIALS_PROJECT.read_text(encoding="utf-8").split())

    for required in (
        "PhaseDiagram.el_refs",
        "thermodynamic compatibility types",
        "zero-temperature database",
        "not an experimental standard state",
        "performs no network request by itself",
        "does not authorize calculator execution",
    ):
        assert required in documentation


def test_local_execution_file_is_documented_as_a_non_authorizing_template() -> None:
    documentation = " ".join(
        LOCAL_EXECUTION.read_text(encoding="utf-8").lower().split()
    )

    assert "operator-only deployment template" in documentation
    assert "no production parser" in documentation
    assert "do not constitute execution authorization" in documentation
