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
    / "docs"
    / "projectkoios/simulations/dft/pseudopotential_repository"
    / "PseudopotentialLibrary/index.md"
)
LOCAL_EXECUTION = REPOSITORY_ROOT / "docs/local-execution.md"
_LINK = re.compile(r"\[[^]]*\]\(([^)]+)\)")


def test_revised_navigation_documents_have_no_broken_relative_links() -> None:
    documents = (
        REPOSITORY_ROOT / "README.md",
        REPOSITORY_ROOT / "examples/README.md",
        REPOSITORY_ROOT / "examples/projectkoios/README.md",
        REPOSITORY_ROOT / "examples/projectkoios/simulations/README.md",
        REPOSITORY_ROOT
        / "docs"
        / "architecture/projectkoios/simulations/workflows/pw_dft_scf/cpn/index.md",
        REPOSITORY_ROOT
        / "docs"
        / "projectkoios/simulations/dft/pseudopotential_repository/index.md",
        REPOSITORY_ROOT
        / "docs/projectkoios/simulations/dft/pseudopotential_repository"
        / "PseudopotentialRepository/index.md",
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
        "## `build_repository(required)`",
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


def test_local_execution_file_is_documented_as_a_non_authorizing_template() -> None:
    documentation = " ".join(
        LOCAL_EXECUTION.read_text(encoding="utf-8").lower().split()
    )

    assert "operator-only deployment template" in documentation
    assert "no production parser" in documentation
    assert "do not constitute execution authorization" in documentation
