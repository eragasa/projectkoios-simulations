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


def test_preserved_historical_license_files_have_declared_identities() -> None:
    transfer = _transfer()

    for origin in transfer["origins"]:
        path = REPOSITORY_ROOT / origin["license_file"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == origin["license_sha256"]


def test_wannier90_extraction_is_bound_to_exact_source_and_dependency() -> None:
    transfer = _transfer()
    extraction = transfer["extractions"][0]

    assert {
        key: extraction[key]
        for key in (
            "component",
            "repository",
            "commit",
            "tree",
            "source_namespace",
            "target_namespace",
            "license_sha256",
        )
    } == {
        "component": "wannier90-native-artifact-parsers",
        "repository": "https://github.com/eragasa/ksdft2effmass",
        "commit": "7bd913151f7e61ed2bdba593df920be36573b502",
        "tree": "4f7ca69afbd1381c0cb736b0efe6b8ac5431acf6",
        "source_namespace": "ksdft2effmass.integration.wannier90",
        "target_namespace": "projectkoios.integrations.wannier90",
        "license_sha256": (
            "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4"
        ),
    }
    assert [subtree["git_tree"] for subtree in extraction["subtrees"]] == [
        "1b5c6cd4a46f2fe70859c3aa1fded938a497e4dc",
        "e5093059c62650e2afe14dccd80f25544e05c1df",
    ]
    dependency = extraction["dependencies"][0]
    assert dependency["source_blob"] == "d98be473e19e17a59563fc7c3e00cca02fd822d3"
    assert dependency["destination_owner"] == "physkit.units.quantities"
    assert dependency["commit"] == "97032f16c9125aa124750508f8513cca9f6dab02"
    assert dependency["blob"] == "686d075852ed01aab0a8d74fdec1be5a440c075d"
    assert len(extraction["file_mappings"]) == 7


def test_wannier90_donor_license_is_the_distribution_license() -> None:
    transfer = _transfer()
    extraction = transfer["extractions"][0]
    path = REPOSITORY_ROOT / extraction["license_file"]

    assert hashlib.sha256(path.read_bytes()).hexdigest() == extraction["license_sha256"]
