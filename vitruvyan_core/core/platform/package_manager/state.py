"""
Package State Manager — tracks installed packages.

State file: .vitruvyan/installed_packages.json
Atomic writes (write to .tmp → rename) to prevent corruption.
"""

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .models import InstalledPackage

logger = logging.getLogger(__name__)


class PackageState:
    """
    Manages the installed packages registry.

    File: .vitruvyan/installed_packages.json

    Usage:
        state = PackageState()
        state.add("service-neural-engine", "2.1.0", "docker_compose", ["9003:8003"])
        installed = state.list_installed()
        state.remove("service-neural-engine")
    """

    def __init__(self, state_dir: Optional[Path] = None):
        self._state_dir = state_dir or self._find_state_dir()
        self._state_file = self._state_dir / "installed_packages.json"
        self._state_dir.mkdir(parents=True, exist_ok=True)

    def _find_state_dir(self) -> Path:
        """Find .vitruvyan directory (same logic as update_manager)."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            return Path(result.stdout.strip()) / ".vitruvyan"
        except Exception:
            return Path.home() / ".vitruvyan"

    def list_installed(self) -> List[InstalledPackage]:
        """Return all installed packages."""
        data = self._read()
        return [
            InstalledPackage(
                name=pkg["name"],
                version=pkg["version"],
                installed_at=pkg["installed_at"],
                install_method=pkg["install_method"],
                status=pkg.get("status", "active"),
                ports=pkg.get("ports", []),
            )
            for pkg in data.get("packages", [])
        ]

    def get(self, package_name: str) -> Optional[InstalledPackage]:
        """Get a specific installed package by name."""
        for pkg in self.list_installed():
            if pkg.name == package_name:
                return pkg
        return None

    def is_installed(self, package_name: str) -> bool:
        """Check if a package is installed."""
        return self.get(package_name) is not None

    def add(
        self,
        name: str,
        version: str,
        install_method: str,
        ports: Optional[List[str]] = None,
    ):
        """Register a newly installed package."""
        data = self._read()
        packages = data.get("packages", [])

        # Remove existing entry if upgrading
        packages = [p for p in packages if p["name"] != name]

        packages.append(
            {
                "name": name,
                "version": version,
                "installed_at": datetime.now(timezone.utc).isoformat(),
                "install_method": install_method,
                "status": "active",
                "ports": ports or [],
            }
        )

        data["packages"] = packages
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._write(data)
        logger.info("Registered package: %s v%s", name, version)

    def remove(self, package_name: str):
        """Remove a package from the installed registry."""
        data = self._read()
        before_count = len(data.get("packages", []))
        data["packages"] = [p for p in data.get("packages", []) if p["name"] != package_name]
        after_count = len(data["packages"])

        if before_count == after_count:
            logger.warning("Package %s was not in installed registry", package_name)
            return

        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._write(data)
        logger.info("Removed package from registry: %s", package_name)

    def set_status(self, package_name: str, status: str):
        """Update package status (active, disabled, error)."""
        data = self._read()
        for pkg in data.get("packages", []):
            if pkg["name"] == package_name:
                pkg["status"] = status
                break
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._write(data)

    def _read(self) -> dict:
        """Read state file."""
        if not self._state_file.exists():
            return {"version": "1.0", "packages": []}
        try:
            with open(self._state_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Corrupted state file %s: %s", self._state_file, e)
            return {"version": "1.0", "packages": []}

    def _write(self, data: dict):
        """Atomic write: write to .tmp then rename."""
        tmp_file = self._state_file.with_suffix(".tmp")
        with open(tmp_file, "w") as f:
            json.dump(data, f, indent=2, sort_keys=False)
        os.replace(str(tmp_file), str(self._state_file))
