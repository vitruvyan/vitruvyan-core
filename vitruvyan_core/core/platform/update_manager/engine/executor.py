"""
Upgrade Executor (Apply/Rollback)

Phase 2 implementation.
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import UpgradePlan

logger = logging.getLogger(__name__)


class UpgradeExecutor:
    """
    Execute upgrade (with automatic rollback on failure).
    
    Methods:
    - apply(plan, manifest_path) → bool (success/failure)
    - rollback() → bool
    - create_snapshot() → str (tag name)
    - run_smoke_tests(manifest_path) → bool
    """
    
    def __init__(self):
        """Initialize executor."""
        self.audit_log_path = self._get_audit_log_path()
        self.last_snapshot_tag: Optional[str] = None
    
    def _get_audit_log_path(self) -> Path:
        """
        Get audit log path (P0 contract: Git repo root).
        
        Returns:
            Path to .vitruvyan/upgrade_history.json
        """
        try:
            # Get Git repo root
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            repo_root = Path(result.stdout.strip())
            
            # Create .vitruvyan directory if needed
            vitruvyan_dir = repo_root / ".vitruvyan"
            vitruvyan_dir.mkdir(exist_ok=True)
            
            return vitruvyan_dir / "upgrade_history.json"
        
        except Exception as e:
            logger.warning(f"Could not determine Git repo root: {e}")
            # Fallback to current directory
            return Path(".vitruvyan/upgrade_history.json")
    
    def apply(
        self,
        plan: UpgradePlan,
        manifest_path: Optional[str] = None
    ) -> bool:
        """
        Execute upgrade.
        
        Steps:
        1. Create snapshot (git tag pre-upgrade-<timestamp>)
        2. Checkout target version
        3. Install dependencies (pip install -e .)
        4. Run smoke tests (call vertical's smoke_tests/run.sh)
        5. If tests pass: confirm + write audit log
        6. If tests fail: rollback automatically
        
        Args:
            plan: UpgradePlan from planner
            manifest_path: Path to vertical_manifest.yaml (for smoke tests)
        
        Returns:
            True if upgrade successful, False if rolled back
        """
        logger.info(f"Executing upgrade: {plan.from_version} → {plan.to_version}")
        
        try:
            # Step 1: Create snapshot
            snapshot_tag = self.create_snapshot()
            logger.info(f"Created snapshot: {snapshot_tag}")
            
            # Step 2: Checkout target version
            self._checkout_version(plan.to_version)
            logger.info(f"Checked out version: {plan.to_version}")
            
            # Step 3: Install dependencies (skip in Phase 2, requires pip isolation)
            # TODO Phase 3: pip install -e . (requires venv management)
            logger.warning("Skipping pip install (Phase 2 limitation)")
            
            # Step 4: Run smoke tests
            if plan.tests_required:
                logger.info(f"Running {len(plan.tests_required)} smoke tests...")
                tests_passed = self.run_smoke_tests(manifest_path)
                
                if not tests_passed:
                    logger.error("Smoke tests failed, initiating rollback")
                    self.rollback()
                    return False
                
                logger.info("✅ Smoke tests passed")
            else:
                logger.warning("No smoke tests configured (risky upgrade)")
            
            # Step 5: Write audit log
            self._write_audit_log(
                from_version=plan.from_version,
                to_version=plan.to_version,
                snapshot_tag=snapshot_tag,
                success=True
            )
            
            logger.info(f"✅ Upgrade completed: {plan.from_version} → {plan.to_version}")
            return True
        
        except Exception as e:
            logger.error(f"Upgrade failed: {e}")
            logger.info("Initiating rollback...")
            self.rollback()
            return False
    
    def rollback(self) -> bool:
        """
        Revert to previous version.
        
        Steps:
        1. Read last snapshot tag from audit log
        2. Checkout snapshot tag
        3. Restore requirements.txt snapshot (TODO Phase 3)
        4. Update audit log
        
        Returns:
            True if rollback successful
        """
        logger.info("Starting rollback...")
        
        try:
            # Read last snapshot from audit log
            if self.last_snapshot_tag:
                snapshot_tag = self.last_snapshot_tag
            else:
                snapshot_tag = self._get_last_snapshot_tag()
            
            if not snapshot_tag:
                logger.error("No snapshot tag found (cannot rollback)")
                return False
            
            logger.info(f"Rolling back to snapshot: {snapshot_tag}")
            
            # Checkout snapshot tag
            subprocess.run(
                ["git", "checkout", snapshot_tag],
                check=True,
                timeout=30
            )
            
            # TODO Phase 3: Restore requirements.txt + pip install
            
            logger.info(f"✅ Rollback completed: restored {snapshot_tag}")
            return True
        
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def create_snapshot(self) -> str:
        """
        Create git tag snapshot.
        
        Format: pre-upgrade-YYYYMMDD-HHMMSS
        
        Returns:
            Tag name (e.g., "pre-upgrade-20260219-183045")
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        tag_name = f"pre-upgrade-{timestamp}"
        
        try:
            # Create lightweight tag
            subprocess.run(
                ["git", "tag", tag_name],
                check=True,
                timeout=5
            )
            
            self.last_snapshot_tag = tag_name
            logger.debug(f"Created snapshot tag: {tag_name}")
            
            return tag_name
        
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create snapshot tag: {e}")
    
    def run_smoke_tests(self, manifest_path: Optional[str] = None) -> bool:
        """
        Call vertical's smoke_tests/run.sh.
        
        Contract:
        - Location: <vertical_root>/smoke_tests/run.sh
        - Exit code: 0=pass, 1=fail, 2=error
        - Timeout: 180s (default) or manifest.smoke_tests_timeout
        
        Args:
            manifest_path: Path to vertical_manifest.yaml
        
        Returns:
            True if tests pass (exit code 0)
        """
        if not manifest_path or not os.path.exists(manifest_path):
            logger.warning("No vertical manifest found (skipping smoke tests)")
            return True  # Non-blocking
        
        # Determine vertical root + smoke test path
        vertical_root = os.path.dirname(os.path.abspath(manifest_path))
        smoke_test_script = os.path.join(vertical_root, "smoke_tests/run.sh")
        
        if not os.path.exists(smoke_test_script):
            logger.warning(f"Smoke tests not found: {smoke_test_script}")
            return True  # Non-blocking
        
        if not os.access(smoke_test_script, os.X_OK):
            logger.error(f"Smoke tests not executable: {smoke_test_script}")
            return False  # Blocking (misconfiguration)
        
        # Read timeout from manifest (default: 180s)
        timeout = 180
        try:
            import yaml
            with open(manifest_path, 'r') as f:
                manifest = yaml.safe_load(f)
                timeout = manifest.get("smoke_tests_timeout", 180)
        except Exception as e:
            logger.warning(f"Could not read smoke_tests_timeout: {e}")
        
        # Execute smoke tests
        logger.info(f"Running smoke tests: {smoke_test_script} (timeout={timeout}s)")
        
        try:
            result = subprocess.run(
                [smoke_test_script],
                cwd=vertical_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Log output
            if result.stdout:
                logger.info(f"Smoke test output:\n{result.stdout}")
            if result.stderr:
                logger.warning(f"Smoke test stderr:\n{result.stderr}")
            
            # Check exit code
            if result.returncode == 0:
                logger.info("✅ Smoke tests passed")
                return True
            else:
                logger.error(f"❌ Smoke tests failed (exit code: {result.returncode})")
                return False
        
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Smoke tests timeout after {timeout}s")
            return False
        
        except Exception as e:
            logger.error(f"❌ Smoke tests error: {e}")
            return False
    
    def _checkout_version(self, version: str) -> None:
        """
        Git checkout target version.
        
        Args:
            version: Git tag (e.g., "v1.2.0" or "1.2.0")

        If the tag is not found locally, attempts to fetch it from the upstream
        remote declared in vertical_manifest.yaml (upstream.remote_name).
        This supports downstream verticals where upstream code lives in a
        separate repository.
        """
        # Normalize version (add 'v' prefix if needed)
        tag = version if version.startswith("v") else f"v{version}"
        
        # Check if tag already exists locally
        tag_exists = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/tags/{tag}"],
            capture_output=True,
            timeout=5,
        ).returncode == 0

        if not tag_exists:
            # Fetch from upstream remote declared in vertical_manifest.yaml
            remote_name = self._get_upstream_remote_name()
            if remote_name:
                logger.info(f"Tag {tag} not found locally — fetching from remote '{remote_name}'")
                try:
                    subprocess.run(
                        ["git", "fetch", remote_name, "--tags"],
                        check=True,
                        capture_output=True,
                        timeout=60,
                    )
                    logger.info(f"Fetched tags from '{remote_name}'")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Could not fetch from '{remote_name}': {e.stderr.decode()}")

        try:
            subprocess.run(
                ["git", "checkout", tag],
                check=True,
                capture_output=True,
                timeout=30,
            )
            logger.debug(f"Checked out tag: {tag}")
        
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to checkout {tag}: {e.stderr.decode()}")

    def _get_upstream_remote_name(self) -> Optional[str]:
        """
        Read upstream.remote_name from vertical_manifest.yaml.

        Returns:
            Remote name (e.g., "upstream") or None if manifest not found.
        """
        try:
            import yaml
            current = os.getcwd()
            while current != "/":
                manifest_path = os.path.join(current, "vertical_manifest.yaml")
                if os.path.exists(manifest_path):
                    with open(manifest_path, "r") as f:
                        manifest = yaml.safe_load(f) or {}
                    return manifest.get("upstream", {}).get("remote_name")
                if os.path.exists(os.path.join(current, ".git")):
                    break
                parent = os.path.dirname(current)
                if parent == current:
                    break
                current = parent
        except Exception as e:
            logger.debug(f"Could not read upstream remote_name from manifest: {e}")
        return None
    
    def _get_last_snapshot_tag(self) -> Optional[str]:
        """
        Read last snapshot tag from audit log.
        
        Returns:
            Snapshot tag name or None
        """
        if not self.audit_log_path.exists():
            return None
        
        try:
            with open(self.audit_log_path, 'r') as f:
                history = json.load(f)
            
            if not history.get("upgrades"):
                return None
            
            # Get last upgrade entry
            last_upgrade = history["upgrades"][-1]
            return last_upgrade.get("snapshot_tag")
        
        except Exception as e:
            logger.warning(f"Could not read audit log: {e}")
            return None
    
    def _write_audit_log(
        self,
        from_version: str,
        to_version: str,
        snapshot_tag: str,
        success: bool
    ) -> None:
        """
        Write upgrade entry to audit log (P0 contract).
        
        Format: {upgrades: [{timestamp, from, to, snapshot_tag, success}]}
        
        Args:
            from_version: Starting version
            to_version: Target version
            snapshot_tag: Pre-upgrade snapshot tag
            success: Whether upgrade succeeded
        """
        # Load existing history
        if self.audit_log_path.exists():
            with open(self.audit_log_path, 'r') as f:
                history = json.load(f)
        else:
            history = {"upgrades": []}
        
        # Append new entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "from_version": from_version,
            "to_version": to_version,
            "snapshot_tag": snapshot_tag,
            "success": success
        }
        history["upgrades"].append(entry)
        
        # Write back
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.audit_log_path, 'w') as f:
            json.dump(history, f, indent=2)
        
        logger.info(f"Audit log updated: {self.audit_log_path}")
