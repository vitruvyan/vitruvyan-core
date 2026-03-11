"""
Package Registry — discovers and parses .vit manifest files.

Searches for manifests in:
  1. Built-in: vitruvyan_core/core/platform/package_manager/packages/manifests/
  2. Custom:   .vitruvyan/custom_packages/
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .models import PackageManifest

logger = logging.getLogger(__name__)


class PackageRegistry:
    """
    Discovers and loads .vit package manifests from local directories.

    Usage:
        registry = PackageRegistry()
        manifests = registry.discover()         # all .vit files
        pkg = registry.get("neural_engine")     # lookup by CLI name
    """

    def __init__(self, extra_paths: Optional[List[str]] = None):
        self._search_paths = self._build_search_paths(extra_paths or [])
        self._cache: Dict[str, PackageManifest] = {}

    def _build_search_paths(self, extra: List[str]) -> List[Path]:
        """Build ordered list of directories to search for .vit files."""
        paths = []

        # Built-in manifests (shipped with core)
        builtin = Path(__file__).parent / "packages" / "manifests"
        if builtin.is_dir():
            paths.append(builtin)

        # Custom user manifests
        try:
            from vitruvyan_core.core.platform.update_manager.engine.executor import (
                UpgradeExecutor,
            )

            executor = UpgradeExecutor()
            custom_dir = executor.audit_log_path.parent / "custom_packages"
            if custom_dir.is_dir():
                paths.append(custom_dir)
        except Exception:
            # Fallback: look relative to CWD
            custom = Path(".vitruvyan") / "custom_packages"
            if custom.is_dir():
                paths.append(custom)

        # Extra paths from caller
        for p in extra:
            path = Path(p)
            if path.is_dir():
                paths.append(path)

        return paths

    def discover(self) -> List[PackageManifest]:
        """
        Scan all search paths for .vit files and parse them.

        Returns:
            List of parsed PackageManifest objects.
        """
        self._cache.clear()
        manifests = []

        for search_dir in self._search_paths:
            for vit_file in sorted(search_dir.glob("*.vit")):
                try:
                    manifest = self._parse_vit_file(vit_file)
                    if manifest:
                        manifests.append(manifest)
                        # Index by multiple lookup keys
                        self._cache[manifest.package_name] = manifest
                        self._cache[manifest.short_name] = manifest
                        self._cache[manifest.cli_name] = manifest
                except Exception as e:
                    logger.warning("Failed to parse %s: %s", vit_file, e)

        logger.info("Discovered %d packages from %d directories", len(manifests), len(self._search_paths))
        return manifests

    def get(self, name: str) -> Optional[PackageManifest]:
        """
        Lookup a package by name (full name, short name, or CLI name).

        Supports:
            get("service-neural-engine")  → exact match
            get("neural-engine")          → short name
            get("neural_engine")          → CLI name (underscore)
        """
        if not self._cache:
            self.discover()

        # Direct cache hit
        if name in self._cache:
            return self._cache[name]

        # Try underscore → hyphen conversion
        hyphen_name = name.replace("_", "-")
        if hyphen_name in self._cache:
            return self._cache[hyphen_name]

        return None

    def list_by_type(self, package_type: str) -> List[PackageManifest]:
        """List all packages of a given type (service, order, vertical, extension)."""
        if not self._cache:
            self.discover()
        seen = set()
        result = []
        for manifest in self._cache.values():
            if manifest.package_type == package_type and manifest.package_name not in seen:
                seen.add(manifest.package_name)
                result.append(manifest)
        return result

    def list_by_tier(self, tier: str) -> List[PackageManifest]:
        """List all packages of a given tier (core, package)."""
        if not self._cache:
            self.discover()
        seen = set()
        result = []
        for manifest in self._cache.values():
            if manifest.tier == tier and manifest.package_name not in seen:
                seen.add(manifest.package_name)
                result.append(manifest)
        return result

    def search(self, query: str) -> List[PackageManifest]:
        """
        Search packages by query string (matches name and description).
        """
        if not self._cache:
            self.discover()

        query_lower = query.lower()
        seen = set()
        results = []
        for manifest in self._cache.values():
            if manifest.package_name in seen:
                continue
            if (
                query_lower in manifest.package_name.lower()
                or query_lower in manifest.description.lower()
                or query_lower in (manifest.sacred_order or "").lower()
            ):
                seen.add(manifest.package_name)
                results.append(manifest)

        return results

    def _parse_vit_file(self, path: Path) -> Optional[PackageManifest]:
        """Parse a .vit YAML file into a PackageManifest."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        if not data or not isinstance(data, dict):
            logger.warning("Empty or invalid .vit file: %s", path)
            return None

        compat = data.get("compatibility", {})
        deps = data.get("dependencies", {})
        install = data.get("installation", {})
        health = data.get("health", {})
        smoke = data.get("smoke_tests", {})
        uninstall = data.get("uninstallation", {})
        ownership = data.get("ownership", {})

        return PackageManifest(
            package_name=data["package_name"],
            package_version=data["package_version"],
            package_type=data["package_type"],
            status=data.get("status", "stable"),
            tier=data.get("tier", "package"),
            description=data.get("description", ""),
            sacred_order=data.get("sacred_order"),
            # Compatibility
            min_core_version=compat.get("min_core_version", "1.0.0"),
            max_core_version=compat.get("max_core_version", "1.x.x"),
            contracts_major=compat.get("contracts_major", 1),
            conflicts_with=compat.get("conflicts_with", []),
            # Dependencies
            required_deps=deps.get("required", []),
            optional_deps=deps.get("optional", []),
            system_deps=deps.get("system", []),
            # Installation
            install_method=install.get("method", "docker_compose"),
            compose_service=install.get("compose_service"),
            compose_file=install.get("compose_file", "infrastructure/docker/docker-compose.yml"),
            dockerfile=install.get("dockerfile"),
            ports=install.get("ports", []),
            env_required=install.get("env_required", []),
            env_optional=install.get("env_optional", []),
            init_commands=install.get("init_commands", []),
            components=install.get("components", []),
            # Health
            health_endpoint=health.get("endpoint"),
            health_interval=health.get("interval", 30),
            health_timeout=health.get("timeout", 10),
            # Smoke tests
            smoke_test_path=smoke.get("path"),
            smoke_test_timeout=smoke.get("timeout", 120),
            # Uninstallation
            preserve_data=uninstall.get("preserve_data", True),
            cleanup_streams=uninstall.get("cleanup_streams", False),
            cleanup_channels=uninstall.get("cleanup_channels", []),
            cleanup_commands=uninstall.get("cleanup_commands", []),
            # Ownership
            team=ownership.get("team", ""),
            contact=ownership.get("contact", ""),
            # Source
            manifest_path=str(path),
        )
