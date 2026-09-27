from __future__ import annotations

import os
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_CHECKOUT_VALUE = os.environ.get("PROJECTKOIOS_KSDFT2EFFMASS_CHECKOUT")
DONOR_CHECKOUT = Path(_CHECKOUT_VALUE).resolve() if _CHECKOUT_VALUE else None
_ALLOWED_ADAPTATION_CLASSES = frozenset(
    {
        "bounded_parsing",
        "cross_artifact_validation",
        "dependency_redirection",
        "inventory_validation",
        "namespace_rewrite",
        "native_order_validation",
        "native_semantics_validation",
        "numeric_validation",
        "public_api_extension",
        "unit_validation",
    }
)


def _transfer() -> dict[str, Any]:
    with (REPOSITORY_ROOT / "TRANSFER.toml").open("rb") as stream:
        return tomllib.load(stream)


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(repository), *arguments),
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _object(repository: Path, commit: str, path: str) -> str:
    return _git(repository, "rev-parse", f"{commit}:{path}")


def test_declared_target_git_objects_prove_substantive_adaptation() -> None:
    extraction = _transfer()["extractions"][0]
    initial_commit = extraction["initial_target_commit"]
    target_commit = extraction["target_commit"]

    assert _git(REPOSITORY_ROOT, "cat-file", "-t", initial_commit) == "commit"
    assert (
        _git(REPOSITORY_ROOT, "rev-parse", f"{initial_commit}^{{tree}}")
        == extraction["initial_target_tree"]
    )
    assert _git(REPOSITORY_ROOT, "cat-file", "-t", target_commit) == "commit"
    assert (
        _git(REPOSITORY_ROOT, "rev-parse", f"{target_commit}^{{tree}}")
        == extraction["target_tree"]
    )
    _git(REPOSITORY_ROOT, "merge-base", "--is-ancestor", initial_commit, target_commit)
    _git(REPOSITORY_ROOT, "merge-base", "--is-ancestor", target_commit, "HEAD")

    mappings = extraction["file_mappings"]
    assert len(mappings) == 7
    for mapping in mappings:
        target_blob = mapping["target_blob"]
        assert _object(REPOSITORY_ROOT, target_commit, mapping["target"]) == target_blob
        assert _git(REPOSITORY_ROOT, "cat-file", "-t", target_blob) == "blob"
        assert _git(REPOSITORY_ROOT, "hash-object", mapping["target"]) == target_blob
        assert mapping["source_blob"] != target_blob

        adaptation_classes = set(mapping["adaptation_classes"])
        assert adaptation_classes
        assert adaptation_classes <= _ALLOWED_ADAPTATION_CLASSES
        assert adaptation_classes.isdisjoint({"copied_unchanged", "namespace_only"})

        description = mapping["adaptation"].casefold()
        assert "copied unchanged" not in description
        assert "namespace rewrite only" not in description
        assert "namespace-only" not in description


@pytest.mark.skipif(
    DONOR_CHECKOUT is None,
    reason="PROJECTKOIOS_KSDFT2EFFMASS_CHECKOUT is not set",
)
def test_declared_donor_git_objects_match_source_checkout() -> None:
    assert DONOR_CHECKOUT is not None
    extraction = _transfer()["extractions"][0]
    commit = extraction["commit"]

    assert _git(DONOR_CHECKOUT, "cat-file", "-t", commit) == "commit"
    assert _git(DONOR_CHECKOUT, "rev-parse", f"{commit}^{{tree}}") == extraction["tree"]
    for subtree in extraction["subtrees"]:
        assert _object(DONOR_CHECKOUT, commit, subtree["path"]) == subtree["git_tree"]
        assert _git(DONOR_CHECKOUT, "cat-file", "-t", subtree["git_tree"]) == "tree"

    for mapping in extraction["file_mappings"]:
        source_blob = mapping["source_blob"]
        assert _object(DONOR_CHECKOUT, commit, mapping["source"]) == source_blob
        assert _git(DONOR_CHECKOUT, "cat-file", "-t", source_blob) == "blob"
