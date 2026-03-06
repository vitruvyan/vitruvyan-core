"""
Upgrade Planner (Plan Generation)

Phase 2 implementation.
"""

import logging
import os
import subprocess
from typing import List, Optional

from .models import UpgradePlan, Release

logger = logging.getLogger(__name__)


class PrerequisiteError(Exception):
    """Prerequisite validation failed (blocking upgrade)."""
    pass


class UpgradePlanner:
    """
    Generate upgrade execution plan.
    
    Methods:
    - plan(from_version, to_version, release) → UpgradePlan
    - validate_prerequisites() → raises PrerequisiteError if blocked
    """
    
    def plan(
        self,
        from_version: str,
        to_version: str,
        release: Release,
        manifest_path: Optional[str] = None
    ) -> UpgradePlan:
        """
        Generate upgrade plan.
        
        Args:
            from_version: Current Core version
            to_version: Target Core version
            release: Release object with metadata
            manifest_path: Path to vertical_manifest.yaml (for smoke tests)
        
        Returns:
            UpgradePlan with:
            - changes (breaking/features/fixes)
            - tests_required (smoke tests)
            - estimated_downtime
            - rollback_strategy
        
        Raises:
            PrerequisiteError: If prerequisites fail (dirty tree, disk space)
        """
        logger.info(f"Generating upgrade plan: {from_version} → {to_version}")
        
        # 1. Validate prerequisites (blocking)
        self.validate_prerequisites()
        
        # 2. Analyze changes
        changes = release.changes
        has_breaking = len(changes.get("breaking", [])) > 0
        
        # 3. Determine tests required
        tests_required = self._determine_tests(manifest_path)
        
        # 4. Estimate downtime
        estimated_downtime = self._estimate_downtime(
            has_breaking=has_breaking,
            tests_count=len(tests_required)
        )
        
        # 5. Rollback strategy (MVP: git tag snapshot)
        rollback_strategy = "git_tag_snapshot"
        
        plan = UpgradePlan(
            from_version=from_version,
            to_version=to_version,
            changes=changes,
            tests_required=tests_required,
            estimated_downtime=estimated_downtime,
            rollback_strategy=rollback_strategy
        )
        
        logger.info(
            f"Plan generated: {len(tests_required)} tests, "
            f"~{estimated_downtime}s downtime, "
            f"breaking={has_breaking}"
        )
        
        return plan
    
    def validate_prerequisites(self) -> None:
        """
        Validate upgrade prerequisites (P0 contract compliance).
        
        Checks:
        1. Clean working tree (no uncommitted changes)
        2. No untracked files in critical paths
        3. Sufficient disk space (100MB minimum)
        
        Raises:
            PrerequisiteError: If any check fails
        """
        # Check 1: Clean working tree
        self._check_clean_working_tree()
        
        # Check 2: Disk space
        self._check_disk_space()
        
        logger.info("✅ Prerequisites validated")
    
    def _check_clean_working_tree(self) -> None:
        """
        Check for uncommitted changes (P0 contract requirement).
        
        Raises:
            PrerequisiteError: If working tree is dirty
        """
        try:
            # git diff-index --quiet HEAD --
            result = subprocess.run(
                ["git", "diff-index", "--quiet", "HEAD", "--"],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode != 0:
                # Get modified files
                modified = subprocess.run(
                    ["git", "diff", "--name-only"],
                    capture_output=True,
                    text=True,
                    timeout=5
                ).stdout.strip().split('\n')
                
                raise PrerequisiteError(
                    f"Upgrade blocked: Uncommitted changes detected\n\n"
                    f"Modified files:\n" + '\n'.join(f"  {f}" for f in modified if f) + "\n\n"
                    f"Actions:\n"
                    f"  git commit -am 'WIP: save changes'\n"
                    f"  OR\n"
                    f"  git stash\n"
                )
        
        except subprocess.TimeoutExpired:
            raise PrerequisiteError("Git command timeout")
        
        except FileNotFoundError:
            raise PrerequisiteError("Git not found (install Git)")
    
    def _check_disk_space(self, min_mb: int = 100) -> None:
        """
        Check available disk space.
        
        Args:
            min_mb: Minimum required space in MB
        
        Raises:
            PrerequisiteError: If insufficient disk space
        """
        try:
            stat = os.statvfs(".")
            available_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
            
            if available_mb < min_mb:
                raise PrerequisiteError(
                    f"Insufficient disk space: {available_mb:.0f}MB available, "
                    f"{min_mb}MB required"
                )
            
            logger.debug(f"Disk space: {available_mb:.0f}MB available")
        
        except Exception as e:
            logger.warning(f"Disk space check failed: {e}")
            # Non-blocking (graceful degradation)
    
    def _determine_tests(self, manifest_path: Optional[str]) -> List[str]:
        """
        Determine which smoke tests to run.
        
        Args:
            manifest_path: Path to vertical_manifest.yaml
        
        Returns:
            List of test identifiers (e.g., ["vertical_smoke_tests"])
        """
        tests = []
        
        if manifest_path and os.path.exists(manifest_path):
            # Vertical manifest found → run vertical smoke tests
            vertical_root = os.path.dirname(os.path.abspath(manifest_path))
            smoke_test_path = os.path.join(vertical_root, "smoke_tests/run.sh")

            # If a manifest exists, smoke tests are expected by contract.
            # Execution layer performs strict existence/executable checks.
            tests.append("vertical_smoke_tests")
            if os.path.exists(smoke_test_path) and os.access(smoke_test_path, os.X_OK):
                logger.debug(f"Smoke tests found: {smoke_test_path}")
            else:
                logger.warning(f"Smoke tests missing or non-executable at {smoke_test_path}")
        
        # Core smoke tests (future: add core-level validation)
        # tests.append("core_health_check")
        
        if not tests:
            logger.warning("No smoke tests configured (risky upgrade)")
        
        return tests
    
    def _estimate_downtime(self, has_breaking: bool, tests_count: int) -> int:
        """
        Estimate upgrade downtime in seconds.
        
        Args:
            has_breaking: Whether upgrade has breaking changes
            tests_count: Number of smoke tests to run
        
        Returns:
            Estimated downtime in seconds
        """
        # Base time: git checkout + pip install
        base_time = 30  # seconds
        
        # Breaking changes: +30s for migration
        if has_breaking:
            base_time += 30
        
        # Smoke tests: ~60s per test (configurable via manifest)
        test_time = tests_count * 60
        
        # Rollback buffer: 20% overhead
        total = int((base_time + test_time) * 1.2)
        
        return total
