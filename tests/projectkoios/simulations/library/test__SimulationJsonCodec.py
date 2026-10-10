from __future__ import annotations

import json

import pytest

from projectkoios.simulations.library.codec import (
    SimulationJsonCodec,
    SimulationSerializationError,
)
from tests.projectkoios.simulations.library.support import silicon_scf_specification


def test_round_trips_canonical_scf_specification() -> None:
    specification = silicon_scf_specification()
    codec = SimulationJsonCodec()

    content = codec.dumps(specification)

    assert codec.loads(content) == specification
    assert content.endswith(b"\n")


def test_rejects_noncanonical_whitespace() -> None:
    codec = SimulationJsonCodec()
    content = codec.dumps(silicon_scf_specification())
    noncanonical = json.dumps(json.loads(content), indent=2).encode()

    with pytest.raises(SimulationSerializationError, match="not canonical"):
        codec.loads(noncanonical)


def test_rejects_duplicate_keys_before_schema_decoding() -> None:
    content = b'{"representation":"pw-dft-scf","representation":"pw-dft-scf"}\n'

    with pytest.raises(SimulationSerializationError, match="invalid simulation JSON"):
        SimulationJsonCodec().loads(content)
