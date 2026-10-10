from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_MANIFEST = (
    REPOSITORY_ROOT / "docs/provenance/deferred-provider-example-main-416be52.tsv"
)
RELOCATION_MANIFEST = (
    REPOSITORY_ROOT / "docs/provenance/workflow-runner-relocation-main-416be52.tsv"
)
SOURCE_MANIFEST_SHA256 = (
    "a941ad9efec74067fcf36dc80e05cc11834dd5a59be75c16f38ad61ad375c87f"
)
RELOCATION_MANIFEST_SHA256 = (
    "e3abc3492cf46b35dd842da5ca849777e5f6e776311e207a7f53513b5e374409"
)
APPLICATIONS_COMMIT = "416be52d539bfbffdbc8a27bd8e13de65404821b"
REPLAY_OVERLAY_COMMIT = "7b687fb23b9877b744bfba3455040db2cbf94292"
HISTORICAL_SIMULATIONS_COMMIT = "24dffe10c29e60afcd5fe07aaacb84921a41a43d"
HISTORICAL_SIMULATIONS_TREE = "b7897a05de39072126e6162ce6e8b8fb25be5f31"
FIXTURE_PATH = "tests/fixtures/pw_dft_scf/campaign-projections.json"
FIXTURE_SHA256 = "bfc9f867474c86d20359a23563cf3d6277928bcf435a126357fd2bdc4732f57e"
OVERLAY_SOURCE_PATH = (
    "examples/projectkoios/applications/pw_dft_scf/providers/quantumespresso/"
    "Si/primitive/convergence/joint/replay.py"
)
EVOLVED_AFTER_RELOCATION = frozenset(
    {
        "examples/workflows/pw_dft_scf/README.md",
        "examples/workflows/pw_dft_scf/campaigns/qe-cutoff.toml",
        "examples/workflows/pw_dft_scf/campaigns/qe-grid.toml",
        "examples/workflows/pw_dft_scf/campaigns/qe-kpoint.toml",
        "examples/workflows/pw_dft_scf/campaigns/qe-single.toml",
        "examples/workflows/pw_dft_scf/campaigns/vasp-cutoff.toml",
        "examples/workflows/pw_dft_scf/campaigns/vasp-grid.toml",
        "examples/workflows/pw_dft_scf/campaigns/vasp-kpoint.toml",
        "examples/workflows/pw_dft_scf/campaigns/vasp-single.toml",
        "tools/pw_dft_scf/README.md",
        "tools/pw_dft_scf/config/README.md",
        "tools/pw_dft_scf/config/catalog.toml",
        "tools/pw_dft_scf/config/runner.toml",
        "tools/pw_dft_scf/configuration.py",
        "tools/pw_dft_scf/environment.py",
        "tools/pw_dft_scf/plot_structure.py",
        "tools/pw_dft_scf/render_inputs.py",
        "tests/examples/test__pw_dft_relaxation_qe_projection.py",
        "tests/tools/pw_dft_scf/test__InputProjectionRunner.py",
        "tests/support/exact_provider_graph_probe.py",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(encoding="utf-8", newline="") as stream:
        return tuple(csv.DictReader(stream, delimiter="\t"))


def test_complete_source_closure_has_explicit_final_dispositions() -> None:
    assert _sha256(SOURCE_MANIFEST) == SOURCE_MANIFEST_SHA256
    assert _sha256(RELOCATION_MANIFEST) == RELOCATION_MANIFEST_SHA256
    source_rows = _rows(SOURCE_MANIFEST)
    relocation_rows = _rows(RELOCATION_MANIFEST)

    assert len(source_rows) == len(relocation_rows) == 55
    assert {row["path"] for row in source_rows} == {
        row["source_path"] for row in relocation_rows
    }
    assert Counter(row["category"] for row in relocation_rows) == {
        "example": 50,
        "test": 3,
        "test-resource": 1,
        "test-support": 1,
    }
    assert Counter(row["disposition"] for row in relocation_rows) == {
        "documentation-consolidated": 17,
        "repository-tool": 13,
        "example-declaration": 12,
        "production-cpn": 4,
        "test": 3,
        "example": 2,
        "example-data": 2,
        "test-resource": 1,
        "test-support": 1,
    }

    destination_paths = {row["destination_path"] for row in relocation_rows}
    assert destination_paths > EVOLVED_AFTER_RELOCATION
    for row in relocation_rows:
        destination = REPOSITORY_ROOT / row["destination_path"]
        assert destination.is_file(), row["destination_path"]
        if row["destination_path"] in EVOLVED_AFTER_RELOCATION:
            continue
        assert len(destination.read_bytes()) == int(row["destination_bytes"])
        assert _sha256(destination) == row["destination_sha256"]


def test_clean_layout_separates_production_tools_and_examples() -> None:
    assert not (
        REPOSITORY_ROOT / "examples/projectkoios/simulations/workflows"
    ).exists()
    assert not (
        REPOSITORY_ROOT / "tests/examples/projectkoios/simulations/workflows"
    ).exists()
    assert not (REPOSITORY_ROOT / "docs/architecture/examples").exists()

    cpn = (
        REPOSITORY_ROOT / "src/python/projectkoios/simulations/workflows/pw_dft_scf/cpn"
    )
    assert {path.name for path in cpn.glob("*.py")} == {
        "__init__.py",
        "net.py",
        "runtime.py",
        "workflow.py",
    }
    assert (REPOSITORY_ROOT / "tools/pw_dft_scf/README.md").is_file()
    assert (
        len(
            tuple(
                (REPOSITORY_ROOT / "examples/workflows/pw_dft_scf/campaigns").glob(
                    "*.toml"
                )
            )
        )
        == 8
    )
    assert (
        len(
            tuple(
                (REPOSITORY_ROOT / "examples/workflows/pw_dft_scf/comparisons").glob(
                    "*.toml"
                )
            )
        )
        == 4
    )


def test_source_closure_uses_exactly_one_approved_replay_overlay() -> None:
    rows = _rows(RELOCATION_MANIFEST)
    overlay_rows = [
        row for row in rows if row["effective_commit"] == REPLAY_OVERLAY_COMMIT
    ]

    assert len(overlay_rows) == 1
    assert overlay_rows[0]["source_path"] == OVERLAY_SOURCE_PATH
    assert overlay_rows[0]["base_commit"] == APPLICATIONS_COMMIT
    assert overlay_rows[0]["adaptation"] == "replay-overlay-and-flattening"
    assert all(
        row["effective_commit"] == APPLICATIONS_COMMIT
        for row in rows
        if row not in overlay_rows
    )

    replay = REPOSITORY_ROOT / overlay_rows[0]["destination_path"]
    replay_text = replay.read_text(encoding="utf-8")
    assert "PwDftScfConvergenceReplayActionizer" in replay_text
    assert "PwDftScfConvergenceReplayer" not in replay_text


def test_campaign_fixture_and_historical_simulations_identity_are_exact() -> None:
    fixture = REPOSITORY_ROOT / FIXTURE_PATH
    assert _sha256(fixture) == FIXTURE_SHA256
    payload = json.loads(fixture.read_bytes())

    assert len(payload["campaigns"]) == 8
    assert payload["simulations_commit"] == HISTORICAL_SIMULATIONS_COMMIT
    assert payload["simulations_tree"] == HISTORICAL_SIMULATIONS_TREE
    tree = subprocess.run(
        (
            "git",
            "-C",
            str(REPOSITORY_ROOT),
            "rev-parse",
            f"{HISTORICAL_SIMULATIONS_COMMIT}^{{tree}}",
        ),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert tree == HISTORICAL_SIMULATIONS_TREE


def test_current_python_surfaces_do_not_import_applications_or_old_examples() -> None:
    invalid: list[tuple[Path, str]] = []
    roots = (
        REPOSITORY_ROOT / "src/python/projectkoios/simulations/workflows",
        REPOSITORY_ROOT / "tools",
        REPOSITORY_ROOT / "examples/workflows",
        REPOSITORY_ROOT / "tests/tools",
        REPOSITORY_ROOT / "tests/examples",
    )
    forbidden = (
        "from projectkoios.applications",
        "import projectkoios.applications",
        "examples.projectkoios",
    )
    for root in roots:
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for value in forbidden:
                if value in text:
                    invalid.append((path.relative_to(REPOSITORY_ROOT), value))

    assert invalid == []
