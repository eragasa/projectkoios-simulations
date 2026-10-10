"""Repository-wide pytest policy for calculator execution."""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the explicit calculator-execution authorization switch."""
    parser.getgroup("projectkoios calculator execution").addoption(
        "--authorize-calculator-execution",
        action="store_true",
        default=False,
        help=(
            "authorize tests marked 'simulation' to launch configured real "
            "calculator executables"
        ),
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Skip real-calculator tests unless this invocation carries authorization."""
    if config.getoption("--authorize-calculator-execution"):
        return

    # Marker selection classifies tests; it is deliberately insufficient as an
    # authority signal. Even ``pytest -m simulation`` remains fail-closed unless
    # the operator also supplies the explicit authorization option above.
    unauthorized = pytest.mark.skip(
        reason=(
            "calculator execution requires --authorize-calculator-execution; "
            "the simulation marker alone grants no authority"
        )
    )
    for item in items:
        if item.get_closest_marker("simulation") is not None:
            item.add_marker(unauthorized)
