from __future__ import annotations

import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_provider_runtime_dependencies_are_declared() -> None:
    with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as stream:
        dependencies = set(tomllib.load(stream)["project"]["dependencies"])

    assert dependencies == {"numpy>=2.3,<3", "physkit>=0.1.0"}
