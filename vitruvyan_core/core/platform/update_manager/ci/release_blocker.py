"""
Release Blocker — CI gate for preventing breaking releases.

Analyzes compatibility test results and blocks release if:
- Any vertical manifest is invalid
- Any active vertical is incompatible with target Core version
- Contract compliance tests fail

Used in GitHub Actions workflows to prevent merge/release.
"""

import json
import sys
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .contract_validator import ContractValidator, ValidationResult, discover_verticals
from ..engine.compatibility import CompatibilityChecker
from ..engine.models import Release


class BlockingReason(Enum):
    """Reasons why a release should be blocked."""

    INVALID_MANIFEST = "invalid_manifest"  # Manifest violates contract
    INCOMPATIBLE_VERTICAL = "incompatible_vertical"  # Version range incompatible
    CONTRACT_VIOLATION = "contract_violation"  # Contract compliance test failed
    NO_VERTICALS = "no_verticals"  # No verticals found (suspicious)


@dataclass
class BlockingReport:
    """Report of why release should be blocked."""

    blocked: bool
    reason: Optional[BlockingReason]
    details: str
    failing_verticals: List[str]
    total_verticals: int

    def to_json(self) -> str:
        """Serialize to JSON for CI artifact."""
        return json.dumps(
            {
                "blocked": self.blocked,
                "reason": self.reason.value if self.reason else None,
                "details": self.details,
                "failing_verticals": self.failing_verticals,
                "total_verticals": self.total_verticals,
            },
            indent=2,
        )

    def exit_code(self) -> int:
        """Return exit code for CI (0 = pass, 1 = block)."""
        return 1 if self.blocked else 0


class ReleaseBlocker:
    """
    CI gate that blocks releases breaking active verticals.

    Usage (in CI):
        blocker = ReleaseBlocker()
        report = blocker.check_release("1.3.0")
        print(report.to_json())
        sys.exit(report.exit_code())
    """

    def __init__(self, repo_root: str = ".", core_contracts_major: int = 1):
        """
        Initialize release blocker.

        Args:
            repo_root: Repository root path
            core_contracts_major: Current contracts major version
        """
        self.repo_root = repo_root
        self.validator = ContractValidator(core_contracts_major=core_contracts_major)
        self.compatibility_checker = CompatibilityChecker()

    def check_release(self, target_version: str) -> BlockingReport:
        """
        Check if release should be blocked.

        Args:
            target_version: Target Core version (e.g., "1.3.0")

        Returns:
            BlockingReport with decision and details
        """
        # 1. Discover all verticals
        manifests = discover_verticals(self.repo_root)
        if not manifests:
            return BlockingReport(
                blocked=True,
                reason=BlockingReason.NO_VERTICALS,
                details="No vertical manifests found (suspicious — at least one expected)",
                failing_verticals=[],
                total_verticals=0,
            )

        # 2. Validate all manifests
        validation_results = self.validator.validate_multiple(manifests)
        invalid_manifests = [r for r in validation_results if not r.valid]
        if invalid_manifests:
            failing = [r.manifest_path for r in invalid_manifests]
            errors = "\n".join(
                [f"{r.manifest_path}: {', '.join(r.errors)}" for r in invalid_manifests]
            )
            return BlockingReport(
                blocked=True,
                reason=BlockingReason.INVALID_MANIFEST,
                details=f"Invalid manifests:\n{errors}",
                failing_verticals=failing,
                total_verticals=len(manifests),
            )

        # 3. Check compatibility with target Core version
        import yaml
        
        incompatible = []
        for manifest_path in manifests:
            # Load manifest as dict
            with open(manifest_path, "r") as f:
                manifest = yaml.safe_load(f)
            
            result = self.compatibility_checker.check(
                current_version="0.0.0",  # Dummy (we only care about target version)
                target_version=target_version,
                manifest=manifest,
            )
            if not result.compatible:
                incompatible.append(manifest_path)

        if incompatible:
            details = "\n".join(
                [f"- {path} (reason: version range mismatch)" for path in incompatible]
            )
            return BlockingReport(
                blocked=True,
                reason=BlockingReason.INCOMPATIBLE_VERTICAL,
                details=f"Incompatible verticals for Core {target_version}:\n{details}",
                failing_verticals=incompatible,
                total_verticals=len(manifests),
            )

        # 4. All checks passed
        return BlockingReport(
            blocked=False,
            reason=None,
            details=f"All {len(manifests)} verticals compatible with Core {target_version}",
            failing_verticals=[],
            total_verticals=len(manifests),
        )

    def check_manifest_compliance(self) -> BlockingReport:
        """
        Check if all verticals comply with UPDATE_SYSTEM_CONTRACT.

        Returns:
            BlockingReport (blocks if any manifest is invalid)
        """
        manifests = discover_verticals(self.repo_root)
        if not manifests:
            return BlockingReport(
                blocked=False,  # May be legitimate (no verticals in repo)
                reason=None,
                details="No vertical manifests found",
                failing_verticals=[],
                total_verticals=0,
            )

        validation_results = self.validator.validate_multiple(manifests)
        invalid_manifests = [r for r in validation_results if not r.valid]

        if invalid_manifests:
            failing = [r.manifest_path for r in invalid_manifests]
            errors = "\n".join(
                [f"{r.manifest_path}:\n  {chr(10).join(r.errors)}" for r in invalid_manifests]
            )
            return BlockingReport(
                blocked=True,
                reason=BlockingReason.CONTRACT_VIOLATION,
                details=f"Contract violations:\n{errors}",
                failing_verticals=failing,
                total_verticals=len(manifests),
            )

        return BlockingReport(
            blocked=False,
            reason=None,
            details=f"All {len(manifests)} verticals comply with UPDATE_SYSTEM_CONTRACT_V1",
            failing_verticals=[],
            total_verticals=len(manifests),
        )


def main():
    """
    CLI entry point for CI workflows.

    Usage:
        python -m vitruvyan_core.core.platform.update_manager.ci.release_blocker 1.3.0
        python -m vitruvyan_core.core.platform.update_manager.ci.release_blocker --check-compliance
    """
    import argparse

    parser = argparse.ArgumentParser(description="Check if release should be blocked")
    parser.add_argument(
        "target_version",
        nargs="?",
        help="Target Core version to check (e.g., '1.3.0')",
    )
    parser.add_argument(
        "--check-compliance",
        action="store_true",
        help="Check manifest compliance only (ignore version)",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root path (default: current directory)",
    )

    args = parser.parse_args()

    blocker = ReleaseBlocker(repo_root=args.repo_root)

    if args.check_compliance:
        report = blocker.check_manifest_compliance()
    elif args.target_version:
        report = blocker.check_release(args.target_version)
    else:
        parser.error("Provide target_version or --check-compliance")
        sys.exit(2)

    # Output JSON report
    print(report.to_json())

    # Exit with appropriate code
    sys.exit(report.exit_code())


if __name__ == "__main__":
    main()
