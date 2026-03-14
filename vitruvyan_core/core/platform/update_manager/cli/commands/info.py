"""
vit info <package> — Show detailed package information

Usage:
    vit info neural_engine
    vit info babel_gardens
    vit info vertical-finance
    vit info frontier-odoo        # shows remote info if not installed locally
"""

import argparse

from vitruvyan_core.core.platform.package_manager.registry import PackageRegistry
from vitruvyan_core.core.platform.package_manager.state import PackageState


def _show_remote_info(package_name: str) -> int:
    """Show info from the remote registry when no local manifest exists."""
    try:
        from vitruvyan_core.core.platform.package_manager.remote import RemoteRegistry
        remote = RemoteRegistry()
        pkg = remote.get_package(package_name)
    except Exception:
        pkg = None

    if not pkg:
        print(f"  Package '{package_name}' not found (local or remote).")
        return 1

    print(f"\n  {'─' * 50}")
    print(f"  {package_name}  [remote]")
    print(f"  {'─' * 50}")
    print(f"  Display:     {pkg.get('display_name', package_name)}")
    print(f"  Type:        {pkg.get('type', '?')}")
    print(f"  License:     {'premium' if pkg.get('license_required') else 'community'}")
    print(f"  Description: {pkg.get('description', '')}")

    latest = pkg.get("latest")
    versions = pkg.get("versions", {})
    if latest:
        print(f"\n  Latest version: {latest}")

    if versions:
        print(f"  Available versions:")
        for ver, info in versions.items():
            print(f"    - {ver} (tag: {info.get('release_tag', '?')})")

    print(f"\n  Install with: vit install {package_name}")
    print()
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Show package details."""
    package_name = args.package

    registry = PackageRegistry()
    state = PackageState()

    manifest = registry.get(package_name)
    if not manifest:
        return _show_remote_info(package_name)

    installed = state.get(manifest.package_name)

    print(f"\n  {'─' * 50}")
    print(f"  {manifest.package_name}")
    print(f"  {'─' * 50}")
    print(f"  Version:     {manifest.package_version}")
    print(f"  Type:        {manifest.package_type}")
    print(f"  Tier:        {manifest.tier}")
    print(f"  Status:      {manifest.status}")
    print(f"  Description: {manifest.description}")

    if manifest.sacred_order:
        print(f"  Sacred Order: {manifest.sacred_order}")

    print(f"\n  Compatibility:")
    print(f"    Core: {manifest.min_core_version} — {manifest.max_core_version}")
    print(f"    Contracts: v{manifest.contracts_major}")

    if manifest.required_deps:
        print(f"\n  Dependencies (required):")
        for dep in manifest.required_deps:
            print(f"    - {dep}")

    if manifest.optional_deps:
        print(f"\n  Dependencies (optional):")
        for dep in manifest.optional_deps:
            print(f"    - {dep}")

    if manifest.system_deps:
        print(f"\n  System requirements:")
        for dep in manifest.system_deps:
            print(f"    - {dep}")

    print(f"\n  Installation:")
    print(f"    Method:  {manifest.install_method}")
    if manifest.compose_service:
        print(f"    Service: {manifest.compose_service}")
    if manifest.ports:
        print(f"    Ports:   {', '.join(manifest.ports)}")
    if manifest.health_endpoint:
        print(f"    Health:  {manifest.health_endpoint}")
    if manifest.env_required:
        print(f"    Required env vars:")
        for var in manifest.env_required:
            print(f"      - {var}")

    if manifest.components:
        print(f"\n  Components:")
        for comp in manifest.components:
            name = comp.get("name", "?")
            desc = comp.get("description", "")
            print(f"    - {name}: {desc}")

    if installed:
        print(f"\n  Local Installation:")
        print(f"    Installed: v{installed.version}")
        print(f"    Since:     {installed.installed_at}")
        print(f"    Status:    {installed.status}")
    else:
        if manifest.tier == "core":
            print(f"\n  Core component — managed via 'vit upgrade'")
        else:
            print(f"\n  Not installed — run 'vit install {manifest.cli_name}'")

    if manifest.team:
        print(f"\n  Ownership:")
        print(f"    Team:    {manifest.team}")
        if manifest.contact:
            print(f"    Contact: {manifest.contact}")

    print()
    return 0


def register_info_command(subparsers: argparse._SubParsersAction):
    """Register 'vit info' subcommand."""
    parser = subparsers.add_parser(
        "info",
        help="Show detailed package information",
        description="Display full details about a .vit package.",
    )
    parser.add_argument("package", help="Package name to inspect")
    parser.set_defaults(func=cmd_info)
