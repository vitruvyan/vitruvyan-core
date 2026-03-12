"""
Unit tests for vitruvyan_core.core.platform.package_manager

Tests:
  - Models: PackageManifest, InstalledPackage, InstallPlan properties
  - Registry: discover, get (multi-key), search, list_by_type, list_by_tier
  - Resolver: dependency ordering, conflict detection, system dep checks
  - State: add, remove, is_installed, atomic writes, corrupted state recovery
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from vitruvyan_core.core.platform.package_manager.models import (
    InstallPlan,
    InstalledPackage,
    PackageManifest,
)
from vitruvyan_core.core.platform.package_manager.registry import PackageRegistry
from vitruvyan_core.core.platform.package_manager.resolver import DependencyResolver
from vitruvyan_core.core.platform.package_manager.state import PackageState


# ── Fixtures ────────────────────────────────────────────────────────


def _make_manifest(**overrides) -> PackageManifest:
    """Build a PackageManifest with sensible defaults."""
    defaults = dict(
        package_name="service-test-pkg",
        package_version="1.0.0",
        package_type="service",
        status="stable",
        tier="package",
        description="A test package",
    )
    defaults.update(overrides)
    return PackageManifest(**defaults)


def _write_vit(directory: Path, name: str, data: dict) -> Path:
    """Write a .vit manifest YAML file to a directory."""
    path = directory / f"{name}.vit"
    with open(path, "w") as f:
        yaml.dump(data, f)
    return path


@pytest.fixture
def tmp_state_dir(tmp_path):
    """Provide a temporary state directory."""
    state_dir = tmp_path / ".vitruvyan"
    state_dir.mkdir()
    return state_dir


@pytest.fixture
def state(tmp_state_dir):
    """Provide a PackageState backed by tmp dir."""
    return PackageState(state_dir=tmp_state_dir)


@pytest.fixture
def manifests_dir(tmp_path):
    """Create a temp dir with sample .vit manifests."""
    d = tmp_path / "manifests"
    d.mkdir()

    _write_vit(d, "service-alpha", {
        "package_name": "service-alpha",
        "package_version": "2.0.0",
        "package_type": "service",
        "status": "stable",
        "tier": "package",
        "description": "Alpha service for testing",
        "dependencies": {"required": [], "system": ["docker"]},
        "installation": {
            "method": "docker_compose",
            "compose_service": "alpha",
            "ports": ["9100:8100"],
        },
        "health": {"endpoint": "http://localhost:9100/health"},
    })

    _write_vit(d, "service-beta", {
        "package_name": "service-beta",
        "package_version": "1.5.0",
        "package_type": "service",
        "status": "beta",
        "tier": "package",
        "description": "Beta service depending on alpha",
        "dependencies": {
            "required": ["service-alpha>=1.0.0"],
            "optional": ["service-gamma>=1.0.0"],
            "system": ["docker"],
        },
        "installation": {
            "method": "docker_compose",
            "compose_service": "beta",
            "ports": ["9101:8101"],
        },
    })

    _write_vit(d, "order-gamma", {
        "package_name": "order-gamma",
        "package_version": "1.0.0",
        "package_type": "order",
        "status": "stable",
        "tier": "core",
        "description": "Gamma sacred order",
        "installation": {"method": "docker_compose", "compose_service": "gamma"},
    })

    _write_vit(d, "vertical-test", {
        "package_name": "vertical-test",
        "package_version": "1.0.0",
        "package_type": "vertical",
        "status": "stable",
        "tier": "package",
        "description": "Test vertical meta-package",
        "dependencies": {
            "required": ["vitruvyan-core>=1.15.0", "service-alpha>=2.0.0"],
            "optional": ["service-beta>=1.0.0"],
            "system": ["docker"],
        },
        "installation": {
            "method": "script",
            "components": [
                {"name": "test-intents", "source": "domains/test/intents.py", "description": "Test intents"},
            ],
        },
    })

    return d


@pytest.fixture
def registry(manifests_dir):
    """Registry backed by temp manifests."""
    reg = PackageRegistry(extra_paths=[str(manifests_dir)])
    # Override search paths to only use our temp dir
    reg._search_paths = [manifests_dir]
    reg.discover()
    return reg


# ═══════════════════════════════════════════════════════════════════
#  MODELS
# ═══════════════════════════════════════════════════════════════════


class TestPackageManifest:

    def test_short_name_strips_prefix(self):
        m = _make_manifest(package_name="service-neural-engine")
        assert m.short_name == "neural-engine"

    def test_short_name_no_prefix(self):
        m = _make_manifest(package_name="standalone")
        assert m.short_name == "standalone"

    def test_cli_name_converts_hyphens(self):
        m = _make_manifest(package_name="service-neural-engine")
        assert m.cli_name == "neural_engine"

    def test_frozen_immutable(self):
        m = _make_manifest()
        with pytest.raises(AttributeError):
            m.package_name = "changed"

    def test_default_values(self):
        m = _make_manifest()
        assert m.install_method == "docker_compose"
        assert m.tier == "package"
        assert m.preserve_data is True
        assert m.ports == []
        assert m.components == []


class TestInstalledPackage:

    def test_basic_creation(self):
        pkg = InstalledPackage(
            name="service-test",
            version="1.0.0",
            installed_at="2026-03-11T10:00:00+00:00",
            install_method="docker_compose",
        )
        assert pkg.name == "service-test"
        assert pkg.status == "active"
        assert pkg.ports == []

    def test_frozen(self):
        pkg = InstalledPackage(
            name="x", version="1.0", installed_at="2026-01-01", install_method="script"
        )
        with pytest.raises(AttributeError):
            pkg.name = "changed"


class TestInstallPlan:

    def test_default_can_proceed(self):
        plan = InstallPlan(target="test-pkg", target_version="1.0.0")
        assert plan.can_proceed is True
        assert plan.install_order == []
        assert plan.conflicts == []

    def test_blocked_plan(self):
        plan = InstallPlan(
            target="test-pkg",
            target_version="1.0.0",
            can_proceed=False,
            block_reason="Missing docker",
        )
        assert plan.can_proceed is False
        assert "docker" in plan.block_reason


# ═══════════════════════════════════════════════════════════════════
#  REGISTRY
# ═══════════════════════════════════════════════════════════════════


class TestPackageRegistry:

    def test_discover_finds_all_manifests(self, registry):
        # 4 manifests in our temp dir
        assert len(registry._cache) > 0
        # Each package is indexed by 3 keys (name, short, cli)
        unique = {m.package_name for m in registry._cache.values()}
        assert len(unique) == 4

    def test_get_by_full_name(self, registry):
        pkg = registry.get("service-alpha")
        assert pkg is not None
        assert pkg.package_version == "2.0.0"

    def test_get_by_short_name(self, registry):
        pkg = registry.get("alpha")
        assert pkg is not None
        assert pkg.package_name == "service-alpha"

    def test_get_by_cli_name(self, registry):
        pkg = registry.get("alpha")
        assert pkg is not None
        assert pkg.package_name == "service-alpha"

    def test_get_underscore_to_hyphen(self, registry):
        # "test_pkg" should not match since no manifest has that name
        # but "vertical-test" → cli_name "test" should work
        pkg = registry.get("test")
        assert pkg is not None
        assert pkg.package_type == "vertical"

    def test_get_nonexistent_returns_none(self, registry):
        assert registry.get("nonexistent-pkg") is None

    def test_list_by_type_service(self, registry):
        services = registry.list_by_type("service")
        names = {s.package_name for s in services}
        assert "service-alpha" in names
        assert "service-beta" in names
        assert "order-gamma" not in names

    def test_list_by_type_order(self, registry):
        orders = registry.list_by_type("order")
        assert len(orders) == 1
        assert orders[0].package_name == "order-gamma"

    def test_list_by_tier_core(self, registry):
        core = registry.list_by_tier("core")
        assert len(core) == 1
        assert core[0].package_name == "order-gamma"

    def test_list_by_tier_package(self, registry):
        pkgs = registry.list_by_tier("package")
        names = {p.package_name for p in pkgs}
        assert "service-alpha" in names
        assert "service-beta" in names
        assert "vertical-test" in names

    def test_search_by_name(self, registry):
        results = registry.search("alpha")
        # "alpha" matches service-alpha (name) and service-beta (dep string)
        assert any(r.package_name == "service-alpha" for r in results)
        assert len(results) >= 1

    def test_search_by_description(self, registry):
        results = registry.search("meta-package")
        assert len(results) == 1
        assert results[0].package_type == "vertical"

    def test_search_no_results(self, registry):
        results = registry.search("xyznonexistent")
        assert results == []

    def test_search_case_insensitive(self, registry):
        results = registry.search("ALPHA")
        assert any(r.package_name == "service-alpha" for r in results)

    def test_parse_invalid_vit_skipped(self, manifests_dir):
        """Invalid YAML should be skipped, not crash."""
        bad = manifests_dir / "bad.vit"
        bad.write_text("not: valid: yaml: [[[")
        reg = PackageRegistry()
        reg._search_paths = [manifests_dir]
        manifests = reg.discover()
        # Should still have our 4 valid manifests
        assert len(manifests) == 4

    def test_empty_vit_skipped(self, manifests_dir):
        (manifests_dir / "empty.vit").write_text("")
        reg = PackageRegistry()
        reg._search_paths = [manifests_dir]
        manifests = reg.discover()
        assert len(manifests) == 4


# ═══════════════════════════════════════════════════════════════════
#  RESOLVER
# ═══════════════════════════════════════════════════════════════════


class TestDependencyResolver:

    def test_resolve_simple_package(self, registry, state):
        resolver = DependencyResolver(registry, state)
        plan = resolver.resolve("service-alpha")
        assert plan.target == "service-alpha"
        assert plan.can_proceed is True
        assert "service-alpha" in plan.install_order

    def test_resolve_with_dependency(self, registry, state):
        resolver = DependencyResolver(registry, state)
        plan = resolver.resolve("service-beta")
        # beta requires alpha → alpha should come first
        assert plan.can_proceed is True
        alpha_idx = plan.install_order.index("service-alpha")
        beta_idx = plan.install_order.index("service-beta")
        assert alpha_idx < beta_idx

    def test_resolve_already_installed_dep(self, registry, state):
        state.add("service-alpha", "2.0.0", "docker_compose", ["9100:8100"])
        resolver = DependencyResolver(registry, state)
        plan = resolver.resolve("service-beta")
        assert "service-alpha" in plan.already_installed
        assert "service-alpha" not in plan.install_order
        assert "service-beta" in plan.install_order

    def test_resolve_nonexistent_package(self, registry, state):
        resolver = DependencyResolver(registry, state)
        plan = resolver.resolve("nonexistent-pkg")
        assert plan.can_proceed is False
        assert "not found" in plan.block_reason

    def test_resolve_vertical_installs_deps(self, registry, state):
        resolver = DependencyResolver(registry, state)
        plan = resolver.resolve("vertical-test")
        # vertical-test requires service-alpha
        assert "service-alpha" in plan.install_order
        assert "vertical-test" in plan.install_order
        # alpha before vertical
        assert plan.install_order.index("service-alpha") < plan.install_order.index("vertical-test")

    def test_conflict_detection_by_port(self, registry, state):
        # Install alpha on port 9100
        state.add("service-alpha", "2.0.0", "docker_compose", ["9100:8100"])
        resolver = DependencyResolver(registry, state)
        # Re-installing same package detects port conflict
        plan = resolver.resolve("service-alpha")
        assert plan.can_proceed is False
        assert any("9100" in c for c in plan.conflicts)

    def test_parse_dep_name_with_version(self):
        assert DependencyResolver._parse_dep_name("service-alpha>=1.0.0") == "service-alpha"
        assert DependencyResolver._parse_dep_name("pkg<=2.0") == "pkg"
        assert DependencyResolver._parse_dep_name("pkg==1.0") == "pkg"
        assert DependencyResolver._parse_dep_name("pkg~=1.0") == "pkg"
        assert DependencyResolver._parse_dep_name("simple-name") == "simple-name"


# ═══════════════════════════════════════════════════════════════════
#  STATE
# ═══════════════════════════════════════════════════════════════════


class TestPackageState:

    def test_empty_state(self, state):
        assert state.list_installed() == []
        assert state.is_installed("anything") is False
        assert state.get("anything") is None

    def test_add_and_get(self, state):
        state.add("service-test", "1.0.0", "docker_compose", ["9000:8000"])
        pkg = state.get("service-test")
        assert pkg is not None
        assert pkg.version == "1.0.0"
        assert pkg.install_method == "docker_compose"
        assert pkg.status == "active"
        assert "9000:8000" in pkg.ports

    def test_is_installed(self, state):
        state.add("pkg-a", "1.0", "script")
        assert state.is_installed("pkg-a") is True
        assert state.is_installed("pkg-b") is False

    def test_remove(self, state):
        state.add("to-remove", "1.0", "docker_compose")
        assert state.is_installed("to-remove") is True
        state.remove("to-remove")
        assert state.is_installed("to-remove") is False

    def test_remove_nonexistent(self, state):
        # Should not raise
        state.remove("never-existed")

    def test_add_upgrade_replaces(self, state):
        state.add("pkg", "1.0", "docker_compose")
        state.add("pkg", "2.0", "docker_compose")
        pkg = state.get("pkg")
        assert pkg.version == "2.0"
        assert len(state.list_installed()) == 1

    def test_set_status(self, state):
        state.add("pkg", "1.0", "docker_compose")
        state.set_status("pkg", "error")
        pkg = state.get("pkg")
        assert pkg.status == "error"

    def test_list_installed_multiple(self, state):
        state.add("a", "1.0", "docker_compose")
        state.add("b", "2.0", "script")
        state.add("c", "3.0", "docker_compose")
        installed = state.list_installed()
        names = {p.name for p in installed}
        assert names == {"a", "b", "c"}

    def test_atomic_write_creates_file(self, tmp_state_dir):
        s = PackageState(state_dir=tmp_state_dir)
        s.add("test", "1.0", "script")
        assert (tmp_state_dir / "installed_packages.json").exists()
        # Verify JSON is valid
        with open(tmp_state_dir / "installed_packages.json") as f:
            data = json.load(f)
        assert len(data["packages"]) == 1

    def test_corrupted_state_recovers(self, tmp_state_dir):
        """Corrupted JSON should not crash, just return empty state."""
        state_file = tmp_state_dir / "installed_packages.json"
        state_file.write_text("{invalid json!!!}")
        s = PackageState(state_dir=tmp_state_dir)
        assert s.list_installed() == []

    def test_state_persists_across_instances(self, tmp_state_dir):
        s1 = PackageState(state_dir=tmp_state_dir)
        s1.add("persistent-pkg", "1.0", "docker_compose")

        s2 = PackageState(state_dir=tmp_state_dir)
        assert s2.is_installed("persistent-pkg") is True
        pkg = s2.get("persistent-pkg")
        assert pkg.version == "1.0"


# ═══════════════════════════════════════════════════════════════════
#  INTEGRATION: Registry + Resolver + State
# ═══════════════════════════════════════════════════════════════════


class TestPackageManagerIntegration:

    def test_builtin_manifests_discoverable(self):
        """The real builtin manifests should be parseable."""
        registry = PackageRegistry()
        manifests = registry.discover()
        assert len(manifests) >= 6
        names = {m.package_name for m in manifests}
        assert "service-neural-engine" in names
        assert "vertical-finance" in names

    def test_builtin_lookup_by_cli_name(self):
        registry = PackageRegistry()
        registry.discover()
        pkg = registry.get("neural_engine")
        assert pkg is not None
        assert pkg.package_name == "service-neural-engine"

    @patch("vitruvyan_core.core.platform.package_manager.resolver.DependencyResolver._is_container_running", return_value=True)
    def test_builtin_vertical_resolve(self, mock_container, tmp_state_dir):
        registry = PackageRegistry()
        registry.discover()
        state = PackageState(state_dir=tmp_state_dir)
        resolver = DependencyResolver(registry, state)
        plan = resolver.resolve("vertical-finance")
        assert plan.can_proceed is True
        assert "service-neural-engine" in plan.install_order
        assert "vertical-finance" in plan.install_order
        # neural-engine before vertical
        ne_idx = plan.install_order.index("service-neural-engine")
        vf_idx = plan.install_order.index("vertical-finance")
        assert ne_idx < vf_idx
