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
            "projectkoios-physkit @ https://github.com/eragasa/"
            "projectkoios-physkit/releases/download/v0.1.2/"
            "projectkoios_physkit-0.1.2-py3-none-any.whl#sha256="
            "79283d64707a4e7aa4dd7fcff85647a957f1f6d4a3894bf0350ea65ac745d38c"
        ),
    }
