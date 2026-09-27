from __future__ import annotations

import os
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest

from tests.support.repository_root import REPOSITORY_ROOT

_CHECKOUT_VALUE = os.environ.get("PROJECTKOIOS_FRANKENSTEIN_CHECKOUT")
SOURCE_CHECKOUT = Path(_CHECKOUT_VALUE).resolve() if _CHECKOUT_VALUE else None


def _transfer() -> dict[str, Any]:
    with (REPOSITORY_ROOT / "TRANSFER.toml").open("rb") as stream:
        return tomllib.load(stream)


def _git(*arguments: str) -> str:
    assert SOURCE_CHECKOUT is not None
    completed = subprocess.run(
        ("git", "-C", str(SOURCE_CHECKOUT), *arguments),
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _source_object(commit: str, path: str) -> str:
    return _git("rev-parse", f"{commit}:{path}")


def _target_files(path: Path) -> tuple[Path, ...]:
    return tuple(
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file()
        and "__pycache__" not in candidate.parts
        and candidate.suffix != ".pyc"
    )


@pytest.mark.skipif(
    SOURCE_CHECKOUT is None,
    reason="PROJECTKOIOS_FRANKENSTEIN_CHECKOUT is not set",
)
def test_declared_source_git_objects_and_example_counts() -> None:
    extraction = _transfer()["extractions"][0]
    commit = extraction["source_commit"]

    assert _git("cat-file", "-t", commit) == "commit"
    assert _git("rev-parse", f"{commit}^{{tree}}") == extraction["source_tree"]

    for subtree in extraction["subtrees"]:
        assert _source_object(commit, subtree["path"]) == subtree["git_tree"]
        assert _git("cat-file", "-t", subtree["git_tree"]) == "tree"

    for inventory in extraction["source_inventories"]:
        assert _source_object(commit, inventory["path"]) == inventory["git_tree"]
        assert _git("cat-file", "-t", inventory["git_tree"]) == "tree"

        source_paths = tuple(
            _git(
                "ls-tree", "-r", "--name-only", commit, "--", inventory["path"]
            ).splitlines()
        )
        exclusion_paths = {
            item["source_path"] for item in extraction["example_exclusions"]
        }
        assert len(source_paths) == inventory["source_file_count"]
        assert exclusion_paths <= set(source_paths)
        assert len(exclusion_paths) == inventory["excluded_source_file_count"]
        assert (
            len(source_paths) - len(exclusion_paths)
            == inventory["retained_source_file_count"]
        )

        added_count = inventory.get("added_compatibility_file_count", 0)
        assert (
            inventory["retained_source_file_count"] + added_count
            == inventory["target_file_count"]
        )
        assert (
            len(_target_files(REPOSITORY_ROOT / inventory["target"]))
            == inventory["target_file_count"]
        )

    for source in extraction["compatibility_sources"]:
        source_commit = source.get("source_commit", commit)
        assert _source_object(source_commit, source["path"]) == source["git_blob"]
        assert _git("cat-file", "-t", source["git_blob"]) == "blob"

    for exclusion in extraction["example_exclusions"]:
        assert _source_object(commit, exclusion["source_path"]) == exclusion["git_blob"]
        assert _git("cat-file", "-t", exclusion["git_blob"]) == "blob"
