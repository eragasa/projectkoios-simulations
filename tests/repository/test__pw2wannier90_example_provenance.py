from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_ROOT = (
    REPOSITORY_ROOT
    / "examples/projectkoios/integrations/quantumespresso/pw2wannier90/Si/"
    "wannier90-3.1.0-example11"
)
NSCF_EXAMPLE_ROOT = (
    REPOSITORY_ROOT
    / "examples/projectkoios/integrations/quantumespresso/pw/nscf/Si/primitive"
)
EXPECTED_FILES = {
    "input/silicon.scf": (
        "370b53e0cf4eb9c99ba0f766bf277a604a5b558485fb407188709491d22231dc",
        611,
    ),
    "input/silicon.nscf": (
        "6bfe71900d579edc2fddae0b2a9da65dc7bc6f28ff77eef819569ed174fccd42",
        3932,
    ),
    "input/silicon.win": (
        "d01fd36ea0dedc6f3463d06b703556771b8f665261d8366ed0f460df6c27e890",
        3761,
    ),
    "input/silicon.pw2wan": (
        "ee38dd37e405914e638fe42aa6ca13357fcf33a2d9ca22973f9cc25a2e294941",
        148,
    ),
}


def _toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def test_original_pw2wannier90_example_bytes_match_the_source_manifest() -> None:
    provenance = _toml(EXAMPLE_ROOT / "source.toml")

    assert provenance["content_classification"] == "non-code simulation inputs"
    assert provenance["copy_mode"] == "byte-for-byte"
    assert provenance["execution_performed"] is False
    assert provenance["scientific_validation_claimed"] is False
    assert provenance["pseudopotential_included"] is False
    assert provenance["upstream"] == {
        "project": "Wannier90",
        "repository": "https://github.com/wannier-developers/wannier90",
        "release": "3.1.0",
        "source_directory": "wannier90-3.1.0/examples/example11",
        "archive_filename": "wannier90-3.1.0.tar.gz",
        "archive_sha256": (
            "40651a9832eb93dec20a8360dd535262c261c34e13c41b6755fa6915c936b254"
        ),
        "source_directory_manifest_sha256": (
            "29a2acef7afedb57b5fad1f84bd6cbe372741788a16e01a99cf9166207038ad2"
        ),
    }
    declared = {
        item["target"]: (item["sha256"], item["byte_size"])
        for item in provenance["files"]
    }
    assert declared == EXPECTED_FILES
    assert {
        str(path.relative_to(EXAMPLE_ROOT))
        for path in EXAMPLE_ROOT.rglob("*")
        if path.is_file()
    } == {"README.md", "source.toml", *EXPECTED_FILES}

    for relative_path, (expected_sha256, expected_size) in EXPECTED_FILES.items():
        path = EXAMPLE_ROOT / relative_path
        assert path.is_file() and not path.is_symlink()
        payload = path.read_bytes()
        assert len(payload) == expected_size
        assert hashlib.sha256(payload).hexdigest() == expected_sha256


def test_stage_local_nscf_example_retains_the_exact_upstream_input() -> None:
    provenance = _toml(NSCF_EXAMPLE_ROOT / "source.toml")
    stage_input = NSCF_EXAMPLE_ROOT / "input/pw.in"
    companion_input = EXAMPLE_ROOT / "input/silicon.nscf"
    payload = stage_input.read_bytes()

    assert not stage_input.is_symlink()
    assert payload == companion_input.read_bytes()
    assert len(payload) == provenance["upstream"]["byte_size"] == 3932
    assert hashlib.sha256(payload).hexdigest() == provenance["upstream"]["sha256"]
    assert provenance["execution_performed"] is False
    assert provenance["scientific_validation_claimed"] is False
    companion = (
        NSCF_EXAMPLE_ROOT / provenance["target"]["companion_source_set"]
    ).resolve()
    assert companion == EXAMPLE_ROOT.resolve()
    assert {
        str(path.relative_to(NSCF_EXAMPLE_ROOT))
        for path in NSCF_EXAMPLE_ROOT.rglob("*")
        if path.is_file()
    } == {
        "README.md",
        "calculation.template.toml",
        "source.toml",
        "input/pw.in",
    }


def test_repository_transfer_record_matches_the_example_manifest() -> None:
    provenance = _toml(EXAMPLE_ROOT / "source.toml")
    transfer = _toml(REPOSITORY_ROOT / "TRANSFER.toml")
    source = next(
        item
        for item in transfer["example_sources"]
        if item["component"] == "quantumespresso-pw2wannier90-silicon-example"
    )

    assert source["source_archive_sha256"] == provenance["upstream"]["archive_sha256"]
    assert (
        source["source_directory_manifest_sha256"]
        == provenance["upstream"]["source_directory_manifest_sha256"]
    )
    assert source["inventory_commit"] == provenance["context"]["commit"]
    assert source["inventory_blob"] == provenance["context"]["inventory_blob"]
    assert source["task_blob"] == provenance["context"]["task_blob"]
    assert source["files"] == provenance["files"]
