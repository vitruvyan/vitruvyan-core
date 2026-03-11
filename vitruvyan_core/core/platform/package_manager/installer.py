"""
Package Installer — executes install/remove operations.

Supports:
  - docker_compose: Start/stop services via docker compose
  - Health checking: Poll endpoints after installation
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

import requests

from .models import PackageManifest
from .state import PackageState

logger = logging.getLogger(__name__)


class PackageInstaller:
    """
    Execute package installation and removal.

    Usage:
        installer = PackageInstaller(state)
        success = installer.install(manifest)
        success = installer.remove(manifest)
    """

    def __init__(self, state: PackageState, repo_root: Optional[Path] = None):
        self.state = state
        self.repo_root = repo_root or self._find_repo_root()

    def _find_repo_root(self) -> Path:
        """Find Git repository root."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            return Path(result.stdout.strip())
        except Exception:
            return Path.cwd()

    def install(self, manifest: PackageManifest, interactive: bool = True) -> bool:
        """
        Install a package from its manifest.

        Steps:
            1. Collect required env vars (if interactive)
            2. Start Docker service
            3. Wait for health check
            4. Register in state

        Returns:
            True if installation succeeded.
        """
        logger.info("Installing %s v%s...", manifest.package_name, manifest.package_version)

        if manifest.install_method == "docker_compose":
            return self._install_docker_compose(manifest, interactive)
        else:
            logger.error("Unsupported install method: %s", manifest.install_method)
            return False

    def remove(self, manifest: PackageManifest, purge: bool = False) -> bool:
        """
        Remove an installed package.

        Steps:
            1. Stop Docker service
            2. Optionally purge data
            3. Remove from state

        Returns:
            True if removal succeeded.
        """
        logger.info("Removing %s...", manifest.package_name)

        if manifest.install_method == "docker_compose":
            return self._remove_docker_compose(manifest, purge)
        else:
            logger.error("Unsupported install method: %s", manifest.install_method)
            return False

    def _install_docker_compose(self, manifest: PackageManifest, interactive: bool) -> bool:
        """Install a service via docker compose."""
        compose_file = self.repo_root / manifest.compose_file
        service_name = manifest.compose_service

        if not compose_file.exists():
            logger.error("Compose file not found: %s", compose_file)
            return False

        if not service_name:
            logger.error("No compose_service defined in manifest")
            return False

        # Collect required env vars
        if interactive and manifest.env_required:
            missing = self._check_env_vars(manifest.env_required)
            if missing:
                print(f"\n  Required environment variables for {manifest.package_name}:")
                for var in missing:
                    print(f"    - {var}")
                print(f"\n  Set them in your .env file or environment before installing.")
                return False

        # Start service
        try:
            cmd = [
                "docker", "compose",
                "-f", str(compose_file),
                "up", "-d", "--build",
                service_name,
            ]
            logger.info("Running: %s", " ".join(cmd))
            result = subprocess.run(
                cmd,
                cwd=str(compose_file.parent),
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                logger.error("Docker compose failed:\n%s", result.stderr)
                return False

        except subprocess.TimeoutExpired:
            logger.error("Docker compose timed out after 300s")
            return False

        # Health check
        if manifest.health_endpoint:
            healthy = self._wait_for_health(
                manifest.health_endpoint,
                timeout=manifest.health_timeout,
                interval=3,
            )
            if not healthy:
                logger.warning(
                    "Health check failed for %s at %s — service may still be starting",
                    manifest.package_name,
                    manifest.health_endpoint,
                )

        # Run init commands
        for cmd_str in manifest.init_commands:
            try:
                subprocess.run(cmd_str, shell=True, check=True, timeout=60)
            except Exception as e:
                logger.warning("Init command failed: %s — %s", cmd_str, e)

        # Register
        self.state.add(
            name=manifest.package_name,
            version=manifest.package_version,
            install_method=manifest.install_method,
            ports=manifest.ports,
        )

        return True

    def _remove_docker_compose(self, manifest: PackageManifest, purge: bool) -> bool:
        """Remove a service via docker compose."""
        compose_file = self.repo_root / manifest.compose_file
        service_name = manifest.compose_service

        if not service_name:
            logger.error("No compose_service defined in manifest")
            return False

        try:
            # Stop and remove container
            cmd = [
                "docker", "compose",
                "-f", str(compose_file),
                "stop", service_name,
            ]
            subprocess.run(cmd, cwd=str(compose_file.parent), capture_output=True, timeout=30)

            cmd = [
                "docker", "compose",
                "-f", str(compose_file),
                "rm", "-f", service_name,
            ]
            subprocess.run(cmd, cwd=str(compose_file.parent), capture_output=True, timeout=30)

        except Exception as e:
            logger.warning("Error stopping service: %s", e)

        # Cleanup commands
        if purge:
            for cmd_str in manifest.cleanup_commands:
                try:
                    subprocess.run(cmd_str, shell=True, timeout=30)
                except Exception as e:
                    logger.warning("Cleanup command failed: %s — %s", cmd_str, e)

        # Unregister
        self.state.remove(manifest.package_name)
        return True

    @staticmethod
    def _check_env_vars(required: list) -> list:
        """Return list of required env vars that are not set."""
        import os

        missing = []
        for var in required:
            # Handle "VAR=default" format
            var_name = var.split("=")[0]
            if not os.environ.get(var_name):
                missing.append(var_name)
        return missing

    @staticmethod
    def _wait_for_health(endpoint: str, timeout: int = 30, interval: int = 3) -> bool:
        """Poll health endpoint until ok or timeout."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                resp = requests.get(endpoint, timeout=5)
                if resp.status_code == 200:
                    return True
            except requests.ConnectionError:
                pass
            time.sleep(interval)
        return False
