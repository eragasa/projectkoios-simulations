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


def test_vasp_extraction_is_bound_to_exact_source_trees() -> None:
    transfer = _transfer()

    extraction = transfer["extractions"][0]
    assert extraction["component"] == "projectkoios.integrations.vasp"
    assert extraction["status"] == "native-format-and-scf-integration"
    assert extraction["source_commit"] == ("3eb562f2d6167ec20d6f2c892c517509a7abf283")
    assert extraction["source_tree"] == "e5daec9f5a16e03f998afb9158a101246acd40d1"
    assert [item["git_tree"] for item in extraction["subtrees"]] == [
        "fa1baa70a40cd221aab7da4ec4e68980506c00df",
        "1a0d251fff584c2c6cacfdfe0bc596bb75230aa4",
        "4f4d5d71750095eb8efc92bf6336095230a0d7cc",
    ]
    inventory = extraction["source_inventories"][0]
    assert inventory["git_tree"] == "b84a7f0fe5ae549179a7c9ddb11c210726813108"
    assert (
        inventory["source_file_count"],
        inventory["retained_source_file_count"],
        inventory["excluded_source_file_count"],
        inventory["target_file_count"],
    ) == (18, 11, 7, 11)
    assert [item["git_blob"] for item in extraction["example_exclusions"]] == [
        "6e83532fcde923909053b92ed02df61d978746ee",
        "e8626e8ed6a442a0abbfe7f399f211cfb28465bb",
        "57a0c96c0d0e50797929c80e9b172f57de39f0d3",
        "76ff2883f252a4163e2d26690535e8ab02b52302",
        "70b46512c60dc68252aa04569b0661a977121a4c",
        "5f540029e83636efd54f1a0c79f3d8ebbc5dc751",
        "6343b3a0880479e220e7f42f6755856b740ec2fa",
    ]
    assert extraction["compatibility_sources"][0]["git_blob"] == (
        "c9f500c376cfaf6dedb557258e76ca7378cc8587"
    )


def test_preserved_historical_license_files_have_declared_identities() -> None:
    transfer = _transfer()

    for origin in transfer["origins"]:
        path = REPOSITORY_ROOT / origin["license_file"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == origin["license_sha256"]
