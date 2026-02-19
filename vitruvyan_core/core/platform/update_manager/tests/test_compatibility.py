"""
Compatibility tests for Update Manager CI gates.

These tests validate:
- All vertical manifests comply with UPDATE_SYSTEM_CONTRACT_V1
- All active verticals are compatible with current Core version
- Smoke tests exist and are executable

Marked with @compatibility_test for CI filtering.
"""

import os
from pathlib import Path

import pytest

from ..ci import ContractValidator, compatibility_test, discover_verticals


@compatibility_test
def test_all_manifests_valid(vertical_manifests, contract_validator):
    """
    CRITICAL: All vertical manifests must comply with UPDATE_SYSTEM_CONTRACT_V1.

    This is a blocking test — CI will fail if any manifest is invalid.
    """
    results = contract_validator.validate_multiple(vertical_manifests)
    invalid = [r for r in results if not r.valid]

    if invalid:
        error_msg = "Manifests violate UPDATE_SYSTEM_CONTRACT_V1:\n"
        for result in invalid:
            error_msg += f"\n{result.manifest_path}:\n"
            for error in result.errors:
                error_msg += f"  - {error}\n"
        pytest.fail(error_msg)


@compatibility_test
def test_active_verticals_have_required_fields(active_verticals, contract_validator):
    """
    Active verticals must have all required fields.

    Checks:
    - domain_name, domain_version, status
    - compatibility section (min/max version, contracts_major, channel)
    - ownership section (team, tech_lead, contact)
    """
    for manifest_path in active_verticals:
        result = contract_validator.validate_manifest(manifest_path)
        assert result.valid, f"Active vertical has invalid manifest: {manifest_path}\nErrors: {result.errors}"


@compatibility_test
def test_version_constraints_valid(vertical_manifests):
    """
    Version constraints must be valid SemVer or wildcard patterns.

    Valid examples:
    - "1.0.0" (exact SemVer)
    - "1.x.x" (major wildcard)
    - "1.2.x" (minor wildcard)
    - "2.0.0-beta.1" (pre-release)

    Invalid examples:
    - "1.x" (incomplete)
    - "latest" (not SemVer)
    - "^1.0.0" (npm syntax not allowed)
    """
    import yaml

    validator = ContractValidator()
    for manifest_path in vertical_manifests:
        with open(manifest_path, "r") as f:
            manifest = yaml.safe_load(f)

        if "compatibility" in manifest:
            compat = manifest["compatibility"]
            min_v = compat.get("min_core_version")
            max_v = compat.get("max_core_version")

            if min_v:
                assert validator._is_valid_version(min_v), (
                    f"Invalid min_core_version in {manifest_path}: {min_v}"
                )

            if max_v:
                assert validator._is_valid_version(max_v), (
                    f"Invalid max_core_version in {manifest_path}: {max_v}"
                )


@compatibility_test
def test_contracts_major_matches_core(vertical_manifests):
    """
    All verticals must use same contracts major version as Core.

    This ensures API compatibility (breaking changes require major bump).
    """
    import yaml

    # Read Core contracts major from environment or default to 1
    core_contracts = int(os.getenv("CORE_CONTRACTS_MAJOR", "1"))

    for manifest_path in vertical_manifests:
        with open(manifest_path, "r") as f:
            manifest = yaml.safe_load(f)

        compat = manifest.get("compatibility", {})
        vertical_contracts = compat.get("contracts_major")

        assert vertical_contracts == core_contracts, (
            f"Contracts major mismatch in {manifest_path}: "
            f"vertical={vertical_contracts}, core={core_contracts}"
        )


@compatibility_test
def test_smoke_tests_exist(active_verticals):
    """
    Active verticals should have smoke tests (recommended, not required).

    Smoke tests location: <vertical_root>/smoke_tests/run.sh
    """
    missing = []
    non_executable = []

    for manifest_path in active_verticals:
        vertical_root = Path(manifest_path).parent
        smoke_test_script = vertical_root / "smoke_tests" / "run.sh"

        if not smoke_test_script.exists():
            missing.append(manifest_path)
        elif not os.access(smoke_test_script, os.X_OK):
            non_executable.append(manifest_path)

    # This is a warning, not a hard failure (smoke tests are recommended)
    if missing:
        pytest.skip(
            f"Missing smoke tests (recommended): {len(missing)} verticals\n"
            + "\n".join(f"  - {p}" for p in missing)
        )

    if non_executable:
        pytest.fail(
            f"Non-executable smoke tests: {len(non_executable)} verticals\n"
            + "\n".join(f"  - {p}" for p in non_executable)
        )


@compatibility_test
def test_update_channel_valid(vertical_manifests):
    """
    Update channel must be "stable" or "beta".

    Invalid channels will cause `vit upgrade` to fail.
    """
    import yaml

    for manifest_path in vertical_manifests:
        with open(manifest_path, "r") as f:
            manifest = yaml.safe_load(f)

        compat = manifest.get("compatibility", {})
        channel = compat.get("update_channel")

        assert channel in {"stable", "beta"}, (
            f"Invalid update_channel in {manifest_path}: {channel} "
            f"(must be 'stable' or 'beta')"
        )


@compatibility_test
def test_smoke_test_timeout_in_range(vertical_manifests):
    """
    Smoke test timeout must be 60-600 seconds.

    This prevents runaway tests from blocking upgrades.
    """
    import yaml

    for manifest_path in vertical_manifests:
        with open(manifest_path, "r") as f:
            manifest = yaml.safe_load(f)

        compat = manifest.get("compatibility", {})
        timeout = compat.get("smoke_tests_timeout")

        if timeout is not None:
            assert 60 <= timeout <= 600, (
                f"Invalid smoke_tests_timeout in {manifest_path}: {timeout} "
                f"(must be 60-600 seconds)"
            )


@compatibility_test
def test_manifest_discovery_works(repo_root):
    """
    Verify manifest discovery finds at least one vertical.

    If this fails, either:
    - No verticals exist (suspicious)
    - Discovery logic is broken
    """
    manifests = discover_verticals(str(repo_root))
    assert len(manifests) > 0, (
        "No vertical manifests found. Expected at least one in:\n"
        "  - examples/verticals/*/vertical_manifest.yaml\n"
        "  - domains/*/vertical_manifest.yaml"
    )


# Parametrized test: runs once per vertical
def test_vertical_manifest_individual(vertical_manifest, contract_validator):
    """
    Individual vertical manifest validation (parametrized test).

    This test runs once per vertical, making it easy to identify which
    specific vertical is failing.
    """
    result = contract_validator.validate_manifest(vertical_manifest)
    assert result.valid, (
        f"Manifest validation failed:\n"
        f"Errors: {result.errors}\n"
        f"Warnings: {result.warnings}"
    )
