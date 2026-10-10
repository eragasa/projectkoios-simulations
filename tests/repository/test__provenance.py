from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tomllib
from importlib.resources import files
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _transfer() -> dict[str, Any]:
    with (REPOSITORY_ROOT / "TRANSFER.toml").open("rb") as stream:
        return tomllib.load(stream)


def _tracked_provenance_metadata() -> tuple[Path, ...]:
    completed = subprocess.run(
        ("git", "-C", str(REPOSITORY_ROOT), "ls-files"),
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    paths = (Path(line) for line in completed.stdout.splitlines())
    return tuple(
        REPOSITORY_ROOT / path
        for path in paths
        if (REPOSITORY_ROOT / path).exists()
        and (
            path.parts[0] == "docs"
            or (len(path.parts) == 1 and path.suffix in {".md", ".toml"})
            or path.name == "NOTICE"
            or path.name == "provenance.json"
        )
    )


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
    assert (
        inventory["excluded_destination_repository"],
        inventory["excluded_destination_namespace"],
        inventory["excluded_capability"],
    ) == ("projectkoios-applications", "projectkoios.applications", "pw_dft_scf")
    assert [item["git_blob"] for item in extraction["example_exclusions"]] == [
        "6e83532fcde923909053b92ed02df61d978746ee",
        "e8626e8ed6a442a0abbfe7f399f211cfb28465bb",
        "57a0c96c0d0e50797929c80e9b172f57de39f0d3",
        "76ff2883f252a4163e2d26690535e8ab02b52302",
        "70b46512c60dc68252aa04569b0661a977121a4c",
        "5f540029e83636efd54f1a0c79f3d8ebbc5dc751",
        "6343b3a0880479e220e7f42f6755856b740ec2fa",
    ]
    assert {item["owner_boundary"] for item in extraction["example_exclusions"]} == {
        "projectkoios.applications"
    }
    assert extraction["compatibility_sources"][0]["git_blob"] == (
        "c9f500c376cfaf6dedb557258e76ca7378cc8587"
    )


def test_quantum_espresso_extraction_is_bound_to_exact_source_trees() -> None:
    transfer = _transfer()

    extraction = transfer["extractions"][1]
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
    assert (
        inventory["excluded_destination_repository"],
        inventory["excluded_destination_namespace"],
        inventory["excluded_capability"],
    ) == ("projectkoios-applications", "projectkoios.applications", "pw_dft_scf")
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
    assert {item["owner_boundary"] for item in extraction["example_exclusions"]} == {
        "projectkoios.applications"
    }
    assert [item["git_blob"] for item in extraction["compatibility_sources"]] == [
        "c9f500c376cfaf6dedb557258e76ca7378cc8587",
        "40d1788c48e37b0b487a54701daa14eb5bf55580",
    ]


def test_lammps_extraction_is_bound_to_exact_recovery_trees() -> None:
    transfer = _transfer()

    extraction = next(
        item
        for item in transfer["extractions"]
        if item["component"] == "projectkoios.integrations.lammps"
    )
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


def test_simulation_workflow_migration_is_bound_to_exact_source_objects() -> None:
    transfer = _transfer()
    extraction = next(
        item
        for item in transfer["extractions"]
        if item["component"] == "projectkoios.simulation_workflows"
    )

    assert extraction["source_commit"] == ("416be52d539bfbffdbc8a27bd8e13de65404821b")
    assert extraction["source_tree"] == "de6257c720fa73caff21b393af4a3fb4858fd617"
    assert extraction["source_transfer_manifest_blob"] == (
        "193d76ce48bb42f82c0aaa79ea4744bf7858d5bc"
    )
    assert [item["git_tree"] for item in extraction["subtrees"]] == [
        "600435334b685ebb59c1e2a576c8562a3645c650",
        "49864081f1bb3b830e8871953ffc0b5d4c81bf36",
        "fd2015353c5e4d5bfad7acca6d1fc5055372c777",
        "379a3d9484b93fef09ebfdd1e7bf9f2e900d136a",
        "dcc982dd429d69a1207976ba1213bb81f9ef9a01",
        "06719ae631cf860ddf322985ca5e3e01d7c4ba78",
    ]
    assert [item["git_blob"] for item in extraction["files"]] == [
        "78d4df81be60d6ba3b8fa17f383181bc07728a3b",
        "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
        "41d8a974b415eaf1f1dab5a1a2cad14bc011e2ea",
        "ada12ab4f88ac2ee2c40e08096fac4e1c48e0129",
    ]
    assert (
        extraction["source_file_count"],
        extraction["post_overlay_source_file_count"],
        extraction["typing_marker_count"],
        extraction["test_module_count"],
        extraction["test_support_file_count"],
        extraction["test_resource_file_count"],
        extraction["documentation_file_count"],
        extraction["deferred_provider_example_file_count"],
    ) == (21, 27, 1, 10, 1, 1, 54, 55)
    assert extraction["replacement_overlay_applied"] is True
    assert extraction["replacement_overlay_commit"] == (
        "7b687fb23b9877b744bfba3455040db2cbf94292"
    )
    assert extraction["replacement_overlay_parent"] == extraction["source_commit"]
    assert extraction["replacement_overlay_tree"] == (
        "0e7c07e76d932fb3f5efc173d0835a9f8e7ba8bc"
    )
    assert (
        extraction["replacement_overlay_delta_path_count"],
        extraction["replacement_overlay_capability_path_count"],
        extraction["replacement_overlay_deferred_provider_example_path_count"],
        extraction["replacement_overlay_source_build_inventory_path_count"],
    ) == (17, 14, 1, 2)
    assert extraction["replacement_overlay_stable_action_identity"] == (
        "projectkoios.applications.pw-dft-scf.convergence-replay"
    )

    manifest = REPOSITORY_ROOT / extraction["deferred_provider_example_manifest"]
    assert (
        hashlib.sha256(manifest.read_bytes()).hexdigest()
        == (extraction["deferred_provider_example_manifest_sha256"])
    )
    assert len(manifest.read_text(encoding="utf-8").splitlines()) == 56

    overlay_manifest = REPOSITORY_ROOT / extraction["replacement_overlay_manifest"]
    assert (
        hashlib.sha256(overlay_manifest.read_bytes()).hexdigest()
        == (extraction["replacement_overlay_manifest_sha256"])
    )
    assert len(overlay_manifest.read_text(encoding="utf-8").splitlines()) == 18


def test_workflow_namespace_relocation_preserves_historical_transfer() -> None:
    transfer = _transfer()
    relocation = transfer["namespace_relocations"][0]

    assert relocation["component"] == "projectkoios.simulations.workflows"
    assert relocation["status"] == ("combined-namespace-and-workflow-runner-relocation")
    assert relocation["source_commit"] == ("0ca21564730015dcf989200858b0a6de3f26a038")
    assert relocation["source_tree"] == ("edabf0a6adfd6f8e050a06a48f94a6c34e543d6f")
    assert relocation["source_namespace"] == ("projectkoios.simulation_workflows")
    assert relocation["target_namespace"] == ("projectkoios.simulations.workflows")
    assert relocation["source_implementation_tree"] == (
        "23414407b631cc4d826570ada6adcbeee7efd24c"
    )
    assert relocation["source_test_tree"] == (
        "637daa4f00c435b852f90546cb7db62047f65973"
    )
    assert relocation["source_documentation_tree"] == (
        "7246eed30e10bc4a4a422e2233e596c6d6c56c1c"
    )
    assert relocation["source_typing_marker_blob"] == (
        "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"
    )
    assert (
        relocation["target_typing_marker_blob"]
        == (relocation["source_typing_marker_blob"])
    )
    assert relocation["target_typing_marker"] == (
        "src/python/projectkoios/simulations/py.typed"
    )
    assert (
        relocation["source_file_count"],
        relocation["relocated_source_file_count"],
        relocation["test_file_count"],
        relocation["source_documentation_index_count"],
    ) == (28, 27, 11, 54)
    assert relocation["workflow_runner_source_commit"] == (
        "416be52d539bfbffdbc8a27bd8e13de65404821b"
    )
    assert relocation["workflow_runner_source_tree"] == (
        "de6257c720fa73caff21b393af4a3fb4858fd617"
    )
    assert (
        relocation["workflow_runner_source_file_count"],
        relocation["workflow_runner_test_file_count"],
        relocation["workflow_runner_fixture_file_count"],
        relocation["workflow_runner_probe_file_count"],
        relocation["workflow_runner_total_path_count"],
    ) == (50, 3, 1, 1, 55)
    assert relocation["workflow_runner_replay_overlay_commit"] == (
        "7b687fb23b9877b744bfba3455040db2cbf94292"
    )
    assert relocation["workflow_runner_replay_overlay_path_count"] == 1
    assert relocation["workflow_runner_fixture_sha256"] == (
        "bfc9f867474c86d20359a23563cf3d6277928bcf435a126357fd2bdc4732f57e"
    )
    assert relocation["workflow_runner_examples_remain_nonproduction"] is False
    assert relocation["workflow_cpn_promoted_to_production"] is True
    assert relocation["workflow_tools_remain_outside_package_discovery"] is True
    assert relocation["compatibility_alias_created"] is False
    assert relocation["stable_action_identity"] == (
        "projectkoios.applications.pw-dft-scf.convergence-replay"
    )
    assert relocation["calculator_execution_performed"] is False
    assert [item["role"] for item in relocation["paths"]] == [
        "implementation",
        "tests",
        "architecture documentation",
        "local CPN implementation",
        "workflow tools",
        "workflow declarations and demonstrations",
        "workflow tool and example tests",
        "workflow-runner fixture",
        "exact provider graph probe",
    ]


def test_materials_project_integration_is_bound_to_exact_ksdft_source() -> None:
    transfer = _transfer()
    extraction = next(
        item
        for item in transfer["extractions"]
        if item["component"] == "projectkoios.integrations.materials_project"
    )

    assert extraction["source_commit"] == ("c47d3cfcee7d4a46b66b14426650d5d811b3848d")
    assert extraction["source_tree"] == "011e125d5c6a9a686643ff96bd20a8b35e4c55d3"
    assert extraction["source_implementation_tree"] == (
        "e3c7a01a94050a4e9e79099186ff872b634f420d"
    )
    assert extraction["source_test_tree"] == (
        "5bd346469a95f14577d9a546e1122d8c074f7ca2"
    )
    assert extraction["calculator_execution_performed"] is False
    assert extraction["network_retrieval_performed"] is False


def test_preserved_historical_license_files_have_declared_identities() -> None:
    transfer = _transfer()

    for origin in transfer["origins"]:
        path = REPOSITORY_ROOT / origin["license_file"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == origin["license_sha256"]


def test_wannier90_extraction_is_bound_to_exact_source_and_dependency() -> None:
    transfer = _transfer()
    extraction = next(
        item
        for item in transfer["extractions"]
        if item["component"] == "wannier90-native-artifact-parsers"
    )

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
    assert dependency["destination_owner"] == "projectkoios.physkit.units.quantities"
    assert dependency["destination_owner_at_extraction"] == ("physkit.units.quantities")
    assert dependency["distribution"] == "projectkoios-physkit>=0.1.0"
    assert dependency["distribution_at_extraction"] == "physkit>=0.1.0"
    assert dependency["commit"] == "97032f16c9125aa124750508f8513cca9f6dab02"
    assert dependency["blob"] == "686d075852ed01aab0a8d74fdec1be5a440c075d"
    assert len(extraction["file_mappings"]) == 7
    assert [item["blob"] for item in extraction["consumer_closure"]] == [
        "15f83f6895102931c7c1f9a3a69eadffff34d3d9",
        "e3799be8926dad6c13ac09a9f00907c7f67aa68f",
        "9abab30964b4985647b8f917e1da17648207d2f6",
        "8b508c43979e6442980b80c9a7edf306b32e33f8",
    ]


def test_physkit_runtime_dependency_has_a_compatible_lower_bound() -> None:
    with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]

    assert "projectkoios-physkit>=0.1.0" in project["dependencies"]
    assert not any("git+" in dependency for dependency in project["dependencies"])
    readme = (REPOSITORY_ROOT / "README.md").read_text()
    assert "projectkoios.integrations.wannier90/provenance.json" in readme

    metadata_paths = _tracked_provenance_metadata()
    relative_paths = {path.relative_to(REPOSITORY_ROOT) for path in metadata_paths}
    assert {
        Path("README.md"),
        Path("THIRD_PARTY_NOTICES.md"),
        Path("TRANSFER.toml"),
        Path("docs/provenance/origins.md"),
        Path(
            "docs/architecture/projectkoios/integrations/wannier90/"
            "provenance/import-closure.md"
        ),
        Path("src/python/projectkoios/integrations/wannier90/provenance.json"),
    } <= relative_paths

    forbidden_claim = re.compile(r"\b(?:pinned|offline|locked|lockfile)\b")
    for path in metadata_paths:
        text = path.read_text(encoding="utf-8")
        contexts = re.split(r"(?m)(?=^#{1,6}\s)|\n\s*\n", text)
        for context in contexts:
            if "physkit" not in context.casefold():
                continue
            assert forbidden_claim.search(context.casefold()) is None, path


def test_wannier90_distribution_resource_binds_provenance() -> None:
    package = files("projectkoios.integrations.wannier90")
    provenance = json.loads(package.joinpath("provenance.json").read_text())

    assert provenance["donor"]["commit"] == ("7bd913151f7e61ed2bdba593df920be36573b502")
    assert len(provenance["source_files"]) == 7
    assert len(provenance["test_files"]) == 18
    assert [entry["blob"] for entry in provenance["consumer_closure"]] == [
        "15f83f6895102931c7c1f9a3a69eadffff34d3d9",
        "e3799be8926dad6c13ac09a9f00907c7f67aa68f",
        "9abab30964b4985647b8f917e1da17648207d2f6",
        "8b508c43979e6442980b80c9a7edf306b32e33f8",
    ]
    physkit = provenance["projectkoios-physkit"]
    assert physkit["distribution"] == "projectkoios-physkit>=0.1.0"
    assert physkit["distribution_at_extraction"] == "physkit>=0.1.0"
    assert physkit["namespace"] == "projectkoios.physkit"
    assert physkit["namespace_at_extraction"] == "physkit"
    assert physkit["license_at_extraction"] == "MIT"
    assert physkit["successor_license"] == "Apache-2.0"


def test_wannier90_donor_license_is_the_distribution_license() -> None:
    transfer = _transfer()
    extraction = next(
        item
        for item in transfer["extractions"]
        if item["component"] == "wannier90-native-artifact-parsers"
    )
    path = REPOSITORY_ROOT / extraction["license_file"]

    assert hashlib.sha256(path.read_bytes()).hexdigest() == extraction["license_sha256"]
