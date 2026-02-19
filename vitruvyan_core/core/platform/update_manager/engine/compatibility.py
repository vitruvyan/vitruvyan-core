"""
Compatibility Checker (Version Validation)

Phase 1 implementation.
"""

import logging
from typing import Optional

from .models import CompatibilityResult

logger = logging.getLogger(__name__)


class CompatibilityChecker:
    """
    Validate Core version against vertical manifest.
    
    Methods:
    - check(current, target, manifest) → CompatibilityResult
    - parse_semver(version) → (major, minor, patch)
    - check_contracts_major(core_contracts, vertical_contracts) → bool
    """
    
    def check(
        self,
        current_version: str,
        target_version: str,
        manifest: dict
    ) -> CompatibilityResult:
        """
        Check if upgrade is compatible.
        
        Args:
            current_version: Current Core version (e.g. "1.0.0")
            target_version: Target Core version (e.g. "1.2.0")
            manifest: vertical_manifest.yaml dict
        
        Returns:
            CompatibilityResult (compatible=True/False + reason)
        
        Blocking conditions:
        - target < manifest.compatibility.min_core_version
        - target > manifest.compatibility.max_core_version
        - contracts_major mismatch
        """
        compatibility = manifest.get("compatibility", {})
        min_version = compatibility.get("min_core_version")
        max_version = compatibility.get("max_core_version")
        contracts_major = compatibility.get("contracts_major")
        
        # Check min_core_version constraint
        if min_version and not self._match_version(target_version, min_version, operator=">="):
            return CompatibilityResult(
                compatible=False,
                blocking_reason=f"Target version {target_version} < min_core_version {min_version}",
                target_version=target_version
            )
        
        # Check max_core_version constraint
        if max_version and not self._match_version(target_version, max_version, operator="<="):
            return CompatibilityResult(
                compatible=False,
                blocking_reason=f"Target version {target_version} > max_core_version {max_version}",
                target_version=target_version
            )
        
        # Check contracts major version (TODO: read from Core metadata)
        # For now, assume Core contracts_version is "1.0.0"
        core_contracts_version = "1.0.0"  # Hardcoded for Phase 1
        if contracts_major is not None:
            core_major = self.parse_semver(core_contracts_version)[0]
            if core_major != contracts_major:
                return CompatibilityResult(
                    compatible=False,
                    blocking_reason=(
                        f"Contracts major mismatch: Core has {core_major}, "
                        f"vertical requires {contracts_major}"
                    ),
                    target_version=target_version
                )
        
        # All checks passed
        logger.info(
            f"Compatibility check passed: {current_version} → {target_version} "
            f"(vertical constraints: {min_version} - {max_version})"
        )
        return CompatibilityResult(
            compatible=True,
            blocking_reason=None,
            target_version=target_version
        )
    
    def _match_version(
        self,
        version: str,
        pattern: str,
        operator: str = "=="
    ) -> bool:
        """
        Match version against pattern with operator.
        
        Args:
            version: SemVer string (e.g., "1.2.3")
            pattern: Constraint pattern (e.g., "1.x.x", "1.2.0")
            operator: Comparison operator ("==", ">=", "<=", ">", "<")
        
        Returns:
            True if version satisfies constraint
        
        Examples:
            _match_version("1.2.3", "1.x.x", "==") → True
            _match_version("1.2.3", "1.0.0", ">=") → True
            _match_version("1.2.3", "2.0.0", "<=") → True
        """
        # Handle wildcard patterns
        if "x" in pattern.lower():
            return self._match_wildcard(version, pattern)
        
        # Handle exact comparison with operators
        version_tuple = self.parse_semver(version)
        pattern_tuple = self.parse_semver(pattern)
        
        if operator == "==":
            return version_tuple == pattern_tuple
        elif operator == ">=":
            return version_tuple >= pattern_tuple
        elif operator == "<=":
            return version_tuple <= pattern_tuple
        elif operator == ">":
            return version_tuple > pattern_tuple
        elif operator == "<":
            return version_tuple < pattern_tuple
        else:
            raise ValueError(f"Unsupported operator: {operator}")
    
    def _match_wildcard(self, version: str, pattern: str) -> bool:
        """
        Match version against wildcard pattern.
        
        Wildcard semantics (P0 contract): "x" = any non-negative integer
        
        Args:
            version: SemVer string (e.g., "1.2.3")
            pattern: Wildcard pattern (e.g., "1.x.x", "1.2.x")
        
        Returns:
            True if version matches pattern
        
        Examples:
            _match_wildcard("1.5.2", "1.x.x") → True
            _match_wildcard("2.0.0", "1.x.x") → False
            _match_wildcard("1.2.99", "1.2.x") → True
        """
        # Strip prerelease/metadata from version
        version_base = version.split("-")[0].split("+")[0]
        
        pattern_parts = pattern.lower().split(".")
        version_parts = version_base.split(".")
        
        # Must have same number of parts
        if len(pattern_parts) != len(version_parts):
            return False
        
        for pattern_part, version_part in zip(pattern_parts, version_parts):
            if pattern_part == "x":
                continue  # Wildcard matches any value
            if pattern_part != version_part:
                return False
        
        return True
    
    def parse_semver(self, version: str) -> tuple:
        """
        Parse SemVer string into comparable tuple.
        
        Args:
            version: SemVer string (e.g., "1.2.3" or "1.2.3-beta.1")
        
        Returns:
            Tuple: (major, minor, patch, prerelease_tuple)
        
        Examples:
            "1.2.3" → (1, 2, 3, ())
            "1.2.0-beta.1" → (1, 2, 0, ('beta', 1))
        """
        # Strip 'v' prefix if present
        version = version.lstrip("v")
        
        # Split version and prerelease
        if "-" in version:
            base_version, prerelease = version.split("-", 1)
        else:
            base_version, prerelease = version, ""
        
        # Parse base version (major.minor.patch)
        parts = base_version.split(".")
        try:
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
        except ValueError:
            logger.warning(f"Invalid SemVer: {version}")
            return (0, 0, 0, ())
        
        # Parse prerelease (beta.1, alpha.2, etc.)
        prerelease_tuple = ()
        if prerelease:
            prerelease_parts = prerelease.split(".")
            prerelease_tuple = tuple(
                int(p) if p.isdigit() else p
                for p in prerelease_parts
            )
        
        return (major, minor, patch, prerelease_tuple)
    
    def check_contracts_major(
        self,
        core_contracts: str,
        vertical_contracts: int
    ) -> bool:
        """
        Check if contracts are compatible (major version only).
        
        Args:
            core_contracts: Core contracts version (e.g., "1.0.0")
            vertical_contracts: Vertical required major version (e.g., 1)
        
        Returns:
            True if major versions match
        """
        core_major = self.parse_semver(core_contracts)[0]
        return core_major == vertical_contracts
        raise NotImplementedError("Phase 1 implementation")
