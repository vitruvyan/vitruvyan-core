"""
Dependency Resolver — builds install plans from .vit manifests.

Implements topological sort for dependency ordering, conflict detection,
and system prerequisite checking.
"""

import logging
import shutil
import subprocess
from typing import Dict, List, Optional, Set

from .models import InstallPlan, PackageManifest
from .state import PackageState

logger = logging.getLogger(__name__)


class DependencyResolver:
    """
    Resolve dependencies and produce an InstallPlan.

    Usage:
        from .registry import PackageRegistry
        from .state import PackageState

        registry = PackageRegistry()
        state = PackageState()
        resolver = DependencyResolver(registry, state)
        plan = resolver.resolve("neural_engine")
    """

    def __init__(self, registry, state: PackageState):
        self.registry = registry
        self.state = state

    def resolve(self, package_name: str) -> InstallPlan:
        """
        Build an install plan for the given package.

        Steps:
          1. Find package manifest
          2. Check system prerequisites (docker, redis, etc.)
          3. Build dependency graph
          4. Topological sort
          5. Filter already-installed
          6. Check conflicts
        """
        manifest = self.registry.get(package_name)
        if not manifest:
            return InstallPlan(
                target=package_name,
                target_version="unknown",
                can_proceed=False,
                block_reason=f"Package '{package_name}' not found in registry",
            )

        # Check conflicts
        conflicts = self._check_conflicts(manifest)
        if conflicts:
            return InstallPlan(
                target=manifest.package_name,
                target_version=manifest.package_version,
                conflicts=conflicts,
                can_proceed=False,
                block_reason=f"Conflicts with installed packages: {', '.join(conflicts)}",
            )

        # Check system deps
        missing_sys = self._check_system_deps(manifest.system_deps)

        # Build install order (topological sort of required deps)
        install_order, already = self._build_install_order(manifest)

        # If system deps missing, we can still show the plan but block
        can_proceed = len(missing_sys) == 0
        block_reason = None
        if missing_sys:
            block_reason = f"Missing system dependencies: {', '.join(missing_sys)}"

        return InstallPlan(
            target=manifest.package_name,
            target_version=manifest.package_version,
            install_order=install_order,
            already_installed=already,
            missing_system_deps=missing_sys,
            conflicts=conflicts,
            can_proceed=can_proceed,
            block_reason=block_reason,
        )

    def _check_conflicts(self, manifest: PackageManifest) -> List[str]:
        """Check if any installed packages conflict with this one."""
        conflicts = []
        installed = self.state.list_installed()
        installed_names = {pkg.name for pkg in installed}

        for conflict_name in manifest.conflicts_with:
            if conflict_name in installed_names:
                conflicts.append(conflict_name)

        # Check port conflicts
        used_ports = set()
        for pkg in installed:
            for port_mapping in pkg.ports:
                host_port = port_mapping.split(":")[0]
                used_ports.add(host_port)

        for port_mapping in manifest.ports:
            host_port = port_mapping.split(":")[0]
            if host_port in used_ports:
                conflicts.append(f"port:{host_port}")

        return conflicts

    def _check_system_deps(self, system_deps: List[str]) -> List[str]:
        """Check which system dependencies are missing."""
        missing = []
        for dep in system_deps:
            if dep == "docker":
                if not shutil.which("docker"):
                    missing.append("docker")
            elif dep == "redis":
                # Redis runs as a container, check if container is running
                if not self._is_container_running("core_redis"):
                    missing.append("redis (container core_redis not running)")
            elif dep == "postgres":
                if not self._is_container_running("core_postgres"):
                    missing.append("postgres (container core_postgres not running)")
            elif dep == "qdrant":
                if not self._is_container_running("core_qdrant"):
                    missing.append("qdrant (container core_qdrant not running)")
        return missing

    def _is_container_running(self, name: str) -> bool:
        """Check if a Docker container is running."""
        try:
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Running}}", name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip() == "true"
        except Exception:
            return False

    def _build_install_order(self, manifest: PackageManifest) -> tuple:
        """
        Build topological install order from dependency graph.

        Returns:
            (install_order, already_installed) — both are lists of package names.
        """
        installed_names = {pkg.name for pkg in self.state.list_installed()}
        install_order: List[str] = []
        already: List[str] = []
        visited: Set[str] = set()

        def visit(pkg_name: str):
            if pkg_name in visited:
                return
            visited.add(pkg_name)

            m = self.registry.get(pkg_name)
            if not m:
                return

            # Visit required dependencies first
            for dep_spec in m.required_deps:
                dep_name = self._parse_dep_name(dep_spec)
                if dep_name and dep_name != "vitruvyan-core":
                    visit(dep_name)

            # Add this package
            if m.package_name in installed_names:
                already.append(m.package_name)
            else:
                install_order.append(m.package_name)

        visit(manifest.package_name)
        return install_order, already

    @staticmethod
    def _parse_dep_name(dep_spec: str) -> Optional[str]:
        """
        Parse dependency name from spec string.

        Examples:
            "service-neural-engine>=2.0.0" → "service-neural-engine"
            "vitruvyan-core>=1.15.0" → "vitruvyan-core"
        """
        for op in [">=", "<=", "==", "~=", "<", ">"]:
            if op in dep_spec:
                return dep_spec.split(op)[0].strip()
        return dep_spec.strip()
