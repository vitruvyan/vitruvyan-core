"""
Pytest integration for Update Manager compatibility tests.

Provides pytest markers, fixtures, and helpers for testing Core compatibility
against all active verticals.

Usage in tests:
    from vitruvyan_core.core.platform.update_manager.ci import compatibility_test

    @compatibility_test
    def test_core_compatible_with_verticals(vertical_manifests):
        for manifest in vertical_manifests:
            validator = ContractValidator()
            result = validator.validate_manifest(manifest)
            assert result.valid, f"Manifest invalid: {result.errors}"
"""

import os
from pathlib import Path
from typing import Callable, List

import pytest

from .contract_validator import ContractValidator, discover_verticals


def compatibility_test(func: Callable) -> Callable:
    """
    Pytest marker for compatibility tests.

    Marks test as 'compatibility' and 'slow' (can be filtered in CI).

    Usage:
        @compatibility_test
        def test_something(vertical_manifests):
            ...
    """
    return pytest.mark.compatibility(pytest.mark.slow(func))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """
    Fixture: Repository root path.

    Searches upward from current directory until finding .git/
    """
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find repository root (no .git found)")


@pytest.fixture(scope="session")
def vertical_manifests(repo_root: Path) -> List[str]:
    """
    Fixture: List of all vertical manifests in repository.

    Discovers manifests in:
    - examples/verticals/*/vertical_manifest.yaml
    - domains/*/vertical_manifest.yaml

    Returns:
        List of absolute paths to vertical_manifest.yaml
    """
    manifests = discover_verticals(str(repo_root))
    if not manifests:
        pytest.skip("No vertical manifests found in repository")
    return manifests


@pytest.fixture(scope="session")
def active_verticals(vertical_manifests: List[str]) -> List[str]:
    """
    Fixture: List of active vertical manifests (status = "active").

    Filters out deprecated/experimental verticals for production CI gates.

    Returns:
        List of paths to active vertical manifests
    """
    import yaml

    active = []
    for manifest_path in vertical_manifests:
        with open(manifest_path, "r") as f:
            manifest = yaml.safe_load(f)
        if manifest.get("status") == "active":
            active.append(manifest_path)

    if not active:
        pytest.skip("No active verticals found")
    return active


@pytest.fixture
def contract_validator() -> ContractValidator:
    """
    Fixture: Initialized ContractValidator.

    Returns:
        ContractValidator instance with current Core contracts version
    """
    # Read Core contracts major version from environment or default to 1
    contracts_major = int(os.getenv("CORE_CONTRACTS_MAJOR", "1"))
    return ContractValidator(core_contracts_major=contracts_major)


@pytest.fixture
def compatibility_check_helper(contract_validator: ContractValidator):
    """
    Fixture: Helper function for compatibility checks.

    Returns:
        Function that validates manifest and raises AssertionError if invalid
    """

    def check(manifest_path: str, allow_warnings: bool = True):
        result = contract_validator.validate_manifest(manifest_path)
        error_msg = f"Manifest validation failed: {manifest_path}\nErrors: {result.errors}"
        if result.warnings and not allow_warnings:
            error_msg += f"\nWarnings: {result.warnings}"
        assert result.valid, error_msg

    return check


def parametrize_verticals(metafunc):
    """
    Pytest hook to parametrize tests with vertical manifests.

    Usage in conftest.py:
        def pytest_generate_tests(metafunc):
            from vitruvyan_core.core.platform.update_manager.ci import parametrize_verticals
            parametrize_verticals(metafunc)

    Then in tests:
        def test_vertical_compatibility(vertical_manifest):
            # This test runs once per vertical
            ...
    """
    if "vertical_manifest" in metafunc.fixturenames:
        manifests = discover_verticals()
        if manifests:
            metafunc.parametrize("vertical_manifest", manifests)
        else:
            # No manifests found, skip test
            metafunc.parametrize("vertical_manifest", [pytest.param(None, marks=pytest.mark.skip)])


# Pytest marker registration (for pytest.ini or pyproject.toml)
PYTEST_MARKERS = """
[tool.pytest.ini_options]
markers = [
    "compatibility: Update Manager compatibility tests (CI gates)",
    "slow: Slow-running tests (can be skipped in dev mode)",
]
"""
