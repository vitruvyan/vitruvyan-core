"""
vit install <package> — Install a .vit package

Usage:
    vit install neural_engine
    vit install mcp --yes
    vit install vertical-finance
"""

import argparse
import sys

from vitruvyan_core.core.platform.package_manager.registry import PackageRegistry
from vitruvyan_core.core.platform.package_manager.resolver import DependencyResolver
from vitruvyan_core.core.platform.package_manager.installer import PackageInstaller
from vitruvyan_core.core.platform.package_manager.state import PackageState


def cmd_install(args: argparse.Namespace) -> int:
    """Execute package installation."""
    package_name = args.package
    skip_confirm = args.yes

    registry = PackageRegistry()
    state = PackageState()
    resolver = DependencyResolver(registry, state)
    installer = PackageInstaller(state)

    # Lookup package
    manifest = registry.get(package_name)
    if not manifest:
        print(f"  Package '{package_name}' not found.")
        print(f"  Use 'vit search {package_name}' to find available packages.")
        return 1

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

    if plan.missing_system_deps:
        print(f"\n  Missing system dependencies:")
        for dep in plan.missing_system_deps:
            print(f"    ! {dep}")

    if not plan.can_proceed:
        print(f"\n  Cannot install: {plan.block_reason}")
        return 1

    # Confirm
    if not skip_confirm:
        print()
        answer = input("  Proceed with installation? [Y/n] ").strip().lower()
        if answer and answer != "y":
            print("  Installation cancelled.")
            return 0

    # Install dependencies first, then target
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

    print(f"\n  Installation complete.")
    if manifest.health_endpoint:
        print(f"  Health: {manifest.health_endpoint}")
    if manifest.ports:
        print(f"  Ports:  {', '.join(manifest.ports)}")

    return 0


def register_install_command(subparsers: argparse._SubParsersAction):
    """Register 'vit install' subcommand."""
    parser = subparsers.add_parser(
        "install",
        help="Install a .vit package",
        description="Install a package from the Vitruvyan package registry.",
    )
    parser.add_argument("package", help="Package name (e.g. neural_engine, mcp, vertical-finance)")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    parser.set_defaults(func=cmd_install)
