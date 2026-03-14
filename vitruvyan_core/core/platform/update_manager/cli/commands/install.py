"""
vit install <package> — Install a .vit package

Usage:
    vit install neural_engine
    vit install mcp --yes
    vit install vertical-finance
    vit install vertical-finance --with-optional
    vit install frontier-odoo              # downloads from remote registry
"""

import argparse
import sys

from vitruvyan_core.core.platform.package_manager.registry import PackageRegistry
from vitruvyan_core.core.platform.package_manager.resolver import DependencyResolver
from vitruvyan_core.core.platform.package_manager.installer import PackageInstaller
from vitruvyan_core.core.platform.package_manager.state import PackageState
from vitruvyan_core.core.platform.package_manager.remote import (
    RemoteRegistry,
    PackageDownloader,
    read_license_token,
)


def _download_remote_package(package_name: str, skip_confirm: bool):
    """
    Attempt to find and download a package from the remote registry.

    Returns a local PackageRegistry that includes the downloaded manifest,
    and the manifest itself — or (None, None) if not found/failed.
    """
    remote = RemoteRegistry()

    try:
        pkg_info = remote.get_package(package_name)
    except RuntimeError as e:
        print(f"  Could not reach remote registry: {e}")
        return None, None

    if not pkg_info:
        return None, None

    # Determine version
    latest = pkg_info.get("latest")
    versions = pkg_info.get("versions", {})
    if not latest or latest not in versions:
        print(f"  Package '{package_name}' found in remote registry but has no published versions.")
        return None, None

    version_info = versions[latest]
    license_required = pkg_info.get("license_required", False)
    license_token = None

    if license_required:
        license_token = read_license_token()
        if not license_token:
            print(f"\n  {package_name} is a premium package and requires a license.")
            print(f"  Set your license token in .vitruvyan/license.key")
            print(f"  or export VIT_LICENSE_TOKEN=<your-token>")
            return None, None

    # Confirm download
    tier_label = "premium" if license_required else "community"
    print(f"\n  Found '{pkg_info.get('display_name', package_name)}' in remote registry ({tier_label})")
    print(f"  Version: {latest}")
    print(f"  {pkg_info.get('description', '')}")

    if not skip_confirm:
        answer = input("\n  Download and install? [Y/n] ").strip().lower()
        if answer and answer != "y":
            print("  Installation cancelled.")
            return None, None

    # Download and extract
    downloader = PackageDownloader()
    try:
        extract_dir = downloader.download_and_extract(
            package_name, latest, version_info, license_token
        )
    except RuntimeError as e:
        print(f"  Download failed: {e}")
        return None, None

    # Create a registry that includes the downloaded manifest.
    # Look up by the original name first; if that fails, use the first
    # manifest found in the tarball (registry key may differ from
    # the manifest's package_name).
    from pathlib import Path
    registry = PackageRegistry(extra_paths=[str(extract_dir)])
    manifest = registry.get(package_name)
    if not manifest:
        # Discover any .vit in the extract dir
        vit_files = list(extract_dir.glob("*.vit"))
        if vit_files:
            import yaml
            with open(vit_files[0], "r") as f:
                data = yaml.safe_load(f)
            if data and "package_name" in data:
                manifest = registry.get(data["package_name"])
    return registry, manifest


def cmd_install(args: argparse.Namespace) -> int:
    """Execute package installation."""
    package_name = args.package
    skip_confirm = args.yes
    with_optional = args.with_optional

    registry = PackageRegistry()
    state = PackageState()
    resolver = DependencyResolver(registry, state)
    installer = PackageInstaller(state)

    # Lookup package (local first, then remote)
    manifest = registry.get(package_name)
    if not manifest:
        print(f"  Package '{package_name}' not found locally. Checking remote registry...")
        registry, manifest = _download_remote_package(package_name, skip_confirm)
        if not manifest:
            print(f"  Package '{package_name}' not found.")
            print(f"  Use 'vit search {package_name}' to find available packages.")
            return 1
        # Re-create resolver with the updated registry
        resolver = DependencyResolver(registry, state)

    # Check if already installed
    if state.is_installed(manifest.package_name):
        existing = state.get(manifest.package_name)
        print(f"  {manifest.package_name} is already installed (v{existing.version}).")
        print(f"  Use 'vit upgrade {package_name}' to update.")
        return 0

    # Core tier packages are not installable via 'vit install'
    if manifest.tier == "core":
        print(f"  {manifest.package_name} is a core component.")
        print(f"  Core components are managed via 'vit upgrade', not 'vit install'.")
        return 1

    # Resolve dependencies
    plan = resolver.resolve(package_name)

    # Show plan
    print(f"\n  Package: {manifest.package_name} v{manifest.package_version}")
    print(f"  Type:    {manifest.package_type} ({manifest.status})")
    print(f"  Desc:    {manifest.description}")

    if plan.install_order:
        print(f"\n  Will install:")
        for pkg_name in plan.install_order:
            m = registry.get(pkg_name)
            version = m.package_version if m else "?"
            print(f"    + {pkg_name} v{version}")

    if plan.already_installed:
        print(f"\n  Already installed:")
        for pkg_name in plan.already_installed:
            print(f"    = {pkg_name}")

    # Handle optional dependencies for verticals
    optional_to_install = []
    if manifest.package_type == "vertical" and manifest.optional_deps:
        opt_available = []
        for dep_spec in manifest.optional_deps:
            dep_name = _parse_dep_name(dep_spec)
            if dep_name and dep_name != "vitruvyan-core":
                dep_manifest = registry.get(dep_name)
                if dep_manifest and not state.is_installed(dep_manifest.package_name):
                    opt_available.append((dep_manifest, dep_spec))

        if opt_available:
            print(f"\n  Optional packages:")
            for dep_m, dep_spec in opt_available:
                print(f"    ? {dep_m.package_name} v{dep_m.package_version} — {dep_m.description}")

            if with_optional:
                optional_to_install = [dep_m for dep_m, _ in opt_available]
                print(f"\n  --with-optional: will install {len(optional_to_install)} optional package(s)")
            elif not skip_confirm:
                answer = input("\n  Install optional packages too? [y/N] ").strip().lower()
                if answer == "y":
                    optional_to_install = [dep_m for dep_m, _ in opt_available]

    # Vertical components display
    if manifest.package_type == "vertical" and manifest.components:
        print(f"\n  Domain components:")
        for comp in manifest.components:
            print(f"    - {comp.get('name', '?')}: {comp.get('description', '')}")

    if plan.missing_system_deps:
        print(f"\n  Missing system dependencies:")
        for dep in plan.missing_system_deps:
            print(f"    ! {dep}")

    if not plan.can_proceed:
        print(f"\n  Cannot install: {plan.block_reason}")
        return 1

    # Confirm
    if not skip_confirm:
        total = len(plan.install_order) + len(optional_to_install)
        print(f"\n  Total packages to install: {total}")
        answer = input("  Proceed with installation? [Y/n] ").strip().lower()
        if answer and answer != "y":
            print("  Installation cancelled.")
            return 0

    # Install required dependencies + target
    for pkg_name in plan.install_order:
        m = registry.get(pkg_name)
        if not m:
            print(f"  Manifest for dependency '{pkg_name}' not found, skipping.")
            continue

        print(f"\n  Installing {m.package_name} v{m.package_version}...")
        success = installer.install(m, interactive=not skip_confirm)
        if success:
            print(f"  {m.package_name} installed.")
        else:
            print(f"  Failed to install {m.package_name}.")
            return 2

    # Install optional dependencies
    for m in optional_to_install:
        print(f"\n  Installing optional: {m.package_name} v{m.package_version}...")
        opt_plan = resolver.resolve(m.package_name)
        for opt_dep in opt_plan.install_order:
            dep_m = registry.get(opt_dep)
            if dep_m and not state.is_installed(dep_m.package_name):
                installer.install(dep_m, interactive=not skip_confirm)
        print(f"  {m.package_name} installed.")

    print(f"\n  Installation complete.")
    if manifest.health_endpoint:
        print(f"  Health: {manifest.health_endpoint}")
    if manifest.ports:
        print(f"  Ports:  {', '.join(manifest.ports)}")

    if manifest.env_optional:
        print(f"\n  Recommended environment variables:")
        for env_var in manifest.env_optional:
            print(f"    {env_var}")

    return 0


def _parse_dep_name(dep_spec: str) -> str:
    """Parse dependency name from spec string."""
    for op in [">=", "<=", "==", "~=", "<", ">"]:
        if op in dep_spec:
            return dep_spec.split(op)[0].strip()
    return dep_spec.strip()


def register_install_command(subparsers: argparse._SubParsersAction):
    """Register 'vit install' subcommand."""
    parser = subparsers.add_parser(
        "install",
        help="Install a .vit package",
        description="Install a package from the Vitruvyan package registry.",
    )
    parser.add_argument("package", help="Package name (e.g. neural_engine, mcp, vertical-finance)")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--with-optional", action="store_true", help="Also install optional dependencies")
    parser.set_defaults(func=cmd_install)
