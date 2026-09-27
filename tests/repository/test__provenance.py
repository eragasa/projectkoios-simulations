from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _transfer() -> dict[str, Any]:
    with (REPOSITORY_ROOT / "TRANSFER.toml").open("rb") as stream:
        return tomllib.load(stream)


def test_transfer_is_bound_to_exact_frankenstein_source_trees() -> None:
    transfer = _transfer()

    assert transfer["source"] == {
        "repository": "https://github.com/eragasa/projectkoios-frankenstein",
        "commit": "3eb562f2d6167ec20d6f2c892c517509a7abf283",
        "tree": "e5daec9f5a16e03f998afb9158a101246acd40d1",
        "subtrees": [
            {
                "role": "implementation",
                "path": "src/projectkoios/frankensteins/simulations",
                "git_tree": "2952b4030c68716c9a25cacb9c9f7ebe4cf0b25a",
                "target": "src/python/projectkoios/simulations",
            },
            {
                "role": "tests",
                "path": "tests/projectkoios/frankensteins/simulations",
                "git_tree": "807a05f2b07dac16dce2f128a2dbd1a2f96bca25",
                "target": "tests/projectkoios/simulations",
            },
            {
                "role": "documentation",
                "path": "docs/projectkoios/frankensteins/simulations",
                "git_tree": "69351637bc876405cc848fef086a5dae787d2233",
                "target": "docs/projectkoios/simulations",
            },
        ],
    }


def test_lammps_extraction_is_bound_to_exact_recovery_trees() -> None:
    transfer = _transfer()

    extraction = transfer["extractions"][0]
    assert extraction["component"] == "projectkoios.integrations.lammps"
    assert extraction["status"] == "reconstruction-scaffold"
    assert extraction["source_commit"] == ("2b996036f84b3cb72a0fc7cc9e7f71095d94ce53")
    assert extraction["source_tree"] == "e0cb377ba799a5a87c3ad9f16958c1ee166a3ed8"
    assert [item["git_tree"] for item in extraction["subtrees"]] == [
        "53fa084f96df6f20706625f5971547b0322d1123",
        "be951fede4d31192b427f756c291501d5164f053",
        "5f3b7bbc3f4e36e8a98e459c8edd94b15050e1e9",
    ]
    assert [item["git_blob"] for item in extraction["compatibility_sources"]] == [
        "9f7d1d0bc8ca55c777d727a252fc21fc93380ac0",
        "75988b31d42bc3cb06a55f51da51f6245a5f3961",
    ]


def test_preserved_historical_license_files_have_declared_identities() -> None:
    transfer = _transfer()

    for origin in transfer["origins"]:
        path = REPOSITORY_ROOT / origin["license_file"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == origin["license_sha256"]
