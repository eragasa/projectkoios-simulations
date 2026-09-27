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


def test_quantum_espresso_extraction_is_bound_to_exact_source_trees() -> None:
    transfer = _transfer()

    extraction = transfer["extractions"][0]
    assert extraction["component"] == ("projectkoios.integrations.quantumespresso")
    assert extraction["status"] == "native-format-and-plane-wave-integration"
    assert extraction["source_commit"] == ("3eb562f2d6167ec20d6f2c892c517509a7abf283")
    assert extraction["source_tree"] == "e5daec9f5a16e03f998afb9158a101246acd40d1"
    assert [item["git_tree"] for item in extraction["subtrees"]] == [
        "b7e9837b6857ba04969507be747d5d4133cbd42c",
        "86bfa8976f02b0f0243b6c994f758392337ddbc9",
        "e5a2525464a548bbb3b4105bdb2bd7cd901fe6cb",
    ]
    inventory = extraction["source_inventories"][0]
    assert inventory["git_tree"] == "293780bc51fa117bfe47981d0da1ee3cb52f59f1"
    assert (
        inventory["source_file_count"],
        inventory["retained_source_file_count"],
        inventory["excluded_source_file_count"],
        inventory["added_compatibility_file_count"],
        inventory["target_file_count"],
    ) == (171, 161, 10, 1, 162)
    assert [item["git_blob"] for item in extraction["example_exclusions"]] == [
        "9dbc3d602ec2f028e0e59a519479f2cf9281f071",
        "472e6a3dabfb01336205274300038ca6ca24dac2",
        "edb91025c4317924db29878ef5eb5ceaa1d39785",
        "a0f33e5766e946387824c4e3bfe354b8d719c124",
        "07ea4d1dd29c3e51313fd20cdf74ffd57bef34c4",
        "ee22a2f3594d11df90a140e5e9f1310699824a09",
        "546214df299427dcad96beacfce1459b935cf845",
        "c1ac4c2374fb57a8bd1fafd35e61a6f44f6a5d64",
        "09dca3452d1e9e611a511b9193d93651845466e4",
        "6e8a34dd48aa20be7cca08c018475e2bbecca2ad",
    ]
    assert [item["git_blob"] for item in extraction["compatibility_sources"]] == [
        "c9f500c376cfaf6dedb557258e76ca7378cc8587",
        "40d1788c48e37b0b487a54701daa14eb5bf55580",
    ]


def test_preserved_historical_license_files_have_declared_identities() -> None:
    transfer = _transfer()

    for origin in transfer["origins"]:
        path = REPOSITORY_ROOT / origin["license_file"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == origin["license_sha256"]
