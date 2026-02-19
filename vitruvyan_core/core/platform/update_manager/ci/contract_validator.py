"""
Contract Validator — UPDATE_SYSTEM_CONTRACT_V1 compliance checker.

Validates:
- Vertical manifest schema (required fields, types, ranges)
- Smoke test existence and executability
- Version constraint semantics (wildcard matching, SemVer)
- Timeout ranges (60-600 seconds)

Used in CI to prevent contract violations before deployment.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ValidationError(Exception):
    """Raised when manifest violates UPDATE_SYSTEM_CONTRACT_V1."""

    pass


@dataclass
class ValidationResult:
    """Result of manifest validation."""

    valid: bool
    errors: List[str]
    warnings: List[str]
    manifest_path: str

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class ContractValidator:
    """
    Validates vertical manifests against UPDATE_SYSTEM_CONTRACT_V1.

    Usage:
        validator = ContractValidator()
        result = validator.validate_manifest("/path/to/vertical_manifest.yaml")
        if not result.valid:
            raise ValidationError(result.errors)
    """

    REQUIRED_FIELDS = {
        "domain_name": str,
        "domain_version": str,
        "status": str,
        "compatibility": dict,
        "ownership": dict,
    }

    REQUIRED_COMPATIBILITY_FIELDS = {
        "min_core_version": str,
        "max_core_version": str,
        "contracts_major": int,
        "update_channel": str,
    }

    REQUIRED_OWNERSHIP_FIELDS = {
        "team": str,
        "tech_lead": str,
        "contact": str,
    }

    VALID_STATUSES = {"active", "deprecated", "experimental"}
    VALID_CHANNELS = {"stable", "beta"}
    SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(-[\w.]+)?$")  # e.g., "1.2.3", "2.0.0-beta.1"
    WILDCARD_PATTERN = re.compile(r"^\d+\.(x|\d+)\.(x|\d+)$")  # e.g., "1.x.x", "1.2.x"

    def __init__(self, core_contracts_major: int = 1):
        """
        Initialize validator.

        Args:
            core_contracts_major: Current Core contracts major version (default 1)
        """
        self.core_contracts_major = core_contracts_major

    def validate_manifest(self, manifest_path: str) -> ValidationResult:
        """
        Validate vertical manifest against contract.

        Args:
            manifest_path: Path to vertical_manifest.yaml

        Returns:
            ValidationResult with errors/warnings
        """
        errors = []
        warnings = []

        # 1. File exists and readable
        if not Path(manifest_path).exists():
            return ValidationResult(
                valid=False,
                errors=[f"Manifest not found: {manifest_path}"],
                warnings=[],
                manifest_path=manifest_path,
            )

        try:
            with open(manifest_path, "r") as f:
                manifest = yaml.safe_load(f)
        except Exception as e:
            return ValidationResult(
                valid=False,
                errors=[f"Failed to parse YAML: {e}"],
                warnings=[],
                manifest_path=manifest_path,
            )

        # 2. Required top-level fields
        for field, expected_type in self.REQUIRED_FIELDS.items():
            if field not in manifest:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(manifest[field], expected_type):
                errors.append(
                    f"Field '{field}' must be {expected_type.__name__}, got {type(manifest[field]).__name__}"
                )

        # 3. Validate 'compatibility' section
        if "compatibility" in manifest and isinstance(manifest["compatibility"], dict):
            compat = manifest["compatibility"]
            for field, expected_type in self.REQUIRED_COMPATIBILITY_FIELDS.items():
                if field not in compat:
                    errors.append(f"Missing compatibility.{field}")
                elif not isinstance(compat[field], expected_type):
                    errors.append(
                        f"compatibility.{field} must be {expected_type.__name__}"
                    )

            # Validate version constraints
            if "min_core_version" in compat and "max_core_version" in compat:
                min_v = compat["min_core_version"]
                max_v = compat["max_core_version"]
                if not self._is_valid_version(min_v):
                    errors.append(f"Invalid min_core_version format: {min_v}")
                if not self._is_valid_version(max_v):
                    errors.append(f"Invalid max_core_version format: {max_v}")

                # Ensure min ≤ max (basic check)
                if self._is_valid_version(min_v) and self._is_valid_version(max_v):
                    if not self._version_lte(min_v, max_v):
                        errors.append(
                            f"min_core_version ({min_v}) > max_core_version ({max_v})"
                        )

            # Validate contracts_major
            if "contracts_major" in compat:
                if compat["contracts_major"] != self.core_contracts_major:
                    errors.append(
                        f"contracts_major mismatch: vertical={compat['contracts_major']}, core={self.core_contracts_major}"
                    )

            # Validate update_channel
            if "update_channel" in compat:
                if compat["update_channel"] not in self.VALID_CHANNELS:
                    errors.append(
                        f"Invalid update_channel: {compat['update_channel']} (must be {self.VALID_CHANNELS})"
                    )

            # Validate smoke_tests_timeout (optional, but must be in range if provided)
            if "smoke_tests_timeout" in compat:
                timeout = compat["smoke_tests_timeout"]
                if not isinstance(timeout, int) or not (60 <= timeout <= 600):
                    errors.append(
                        f"smoke_tests_timeout must be 60-600 seconds, got {timeout}"
                    )

        # 4. Validate 'ownership' section
        if "ownership" in manifest and isinstance(manifest["ownership"], dict):
            owner = manifest["ownership"]
            for field, expected_type in self.REQUIRED_OWNERSHIP_FIELDS.items():
                if field not in owner:
                    errors.append(f"Missing ownership.{field}")
                elif not isinstance(owner[field], expected_type):
                    errors.append(f"ownership.{field} must be {expected_type.__name__}")

            # Validate email format (basic check)
            if "contact" in owner and isinstance(owner["contact"], str):
                if "@" not in owner["contact"]:
                    warnings.append(
                        f"ownership.contact should be an email address: {owner['contact']}"
                    )

        # 5. Validate 'status' field
        if "status" in manifest:
            if manifest["status"] not in self.VALID_STATUSES:
                errors.append(
                    f"Invalid status: {manifest['status']} (must be {self.VALID_STATUSES})"
                )

        # 6. Validate smoke tests exist (if manifest path is in vertical root)
        vertical_root = Path(manifest_path).parent
        smoke_test_script = vertical_root / "smoke_tests" / "run.sh"
        if not smoke_test_script.exists():
            warnings.append(
                f"Smoke test script not found: {smoke_test_script} (recommended for safe upgrades)"
            )
        elif not os.access(smoke_test_script, os.X_OK):
            warnings.append(f"Smoke test script not executable: {smoke_test_script}")

        # Final result
        valid = len(errors) == 0
        return ValidationResult(
            valid=valid, errors=errors, warnings=warnings, manifest_path=manifest_path
        )

    def validate_multiple(self, manifest_paths: List[str]) -> List[ValidationResult]:
        """
        Validate multiple manifests.

        Args:
            manifest_paths: List of paths to vertical_manifest.yaml files

        Returns:
            List of ValidationResult (one per manifest)
        """
        return [self.validate_manifest(path) for path in manifest_paths]

    def _is_valid_version(self, version: str) -> bool:
        """Check if version is valid SemVer or wildcard pattern."""
        return bool(
            self.SEMVER_PATTERN.match(version)
            or self.WILDCARD_PATTERN.match(version)
        )

    def _version_lte(self, v1: str, v2: str) -> bool:
        """
        Check if v1 <= v2 (basic SemVer comparison, ignores wildcards).

        Args:
            v1: First version (e.g., "1.0.0")
            v2: Second version (e.g., "1.x.x" or "2.0.0")

        Returns:
            True if v1 <= v2
        """
        # Strip wildcards for comparison (wildcard = max allowed)
        v1_parts = v1.replace("x", "999").split("-")[0].split(".")
        v2_parts = v2.replace("x", "999").split("-")[0].split(".")

        for p1, p2 in zip(v1_parts, v2_parts):
            if int(p1) < int(p2):
                return True
            elif int(p1) > int(p2):
                return False
        return True  # equal


def discover_verticals(root_dir: str = ".") -> List[str]:
    """
    Discover all vertical manifests in repository.

    Searches for paths matching:
    - examples/verticals/*/vertical_manifest.yaml
    - domains/*/vertical_manifest.yaml

    Args:
        root_dir: Repository root path (default current directory)

    Returns:
        List of absolute paths to vertical_manifest.yaml files
    """
    manifests = []
    root_path = Path(root_dir).resolve()

    # Search in examples/verticals/
    examples_dir = root_path / "examples" / "verticals"
    if examples_dir.exists():
        for vertical_dir in examples_dir.iterdir():
            if vertical_dir.is_dir():
                manifest = vertical_dir / "vertical_manifest.yaml"
                if manifest.exists():
                    manifests.append(str(manifest))

    # Search in domains/
    domains_dir = root_path / "domains"
    if domains_dir.exists():
        for domain_dir in domains_dir.iterdir():
            if domain_dir.is_dir():
                manifest = domain_dir / "vertical_manifest.yaml"
                if manifest.exists():
                    manifests.append(str(manifest))

    return manifests
