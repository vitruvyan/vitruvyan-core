"""
Pytest configuration for Update Manager tests.

Registers markers and configures test parametrization for vertical manifests.
"""

import pytest

# Import fixtures from pytest_integration module
from ..ci.pytest_integration import (
    repo_root,
    vertical_manifests,
    active_verticals,
    contract_validator,
    compatibility_check_helper,
    parametrize_verticals,
)


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "compatibility: Update Manager compatibility tests (CI gates)",
    )
    config.addinivalue_line(
        "markers",
        "slow: Slow-running tests (can be skipped with -m 'not slow')",
    )


def pytest_generate_tests(metafunc):
    """Parametrize tests with vertical manifests."""
    parametrize_verticals(metafunc)
