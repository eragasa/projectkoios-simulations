from __future__ import annotations

import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_provider_runtime_dependencies_are_declared() -> None:
    with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as stream:
        dependencies = set(tomllib.load(stream)["project"]["dependencies"])

    assert dependencies == {
        "numpy>=2.3,<3",
        (
            "projectkoios-physkit @ git+https://github.com/eragasa/"
            "projectkoios-physkit.git@"
            "7120b735c7e3e450aa8924780a71deb59d812632"
        ),
    }
