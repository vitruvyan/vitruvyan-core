"""
vit list — Show installed packages and available packages

Usage:
    vit list                    # installed packages
    vit list --all              # all available packages
    vit list --type service     # filter by type
"""

import argparse

from vitruvyan_core.core.platform.package_manager.registry import PackageRegistry
from vitruvyan_core.core.platform.package_manager.state import PackageState


def cmd_list(args: argparse.Namespace) -> int:
    """List packages."""
    show_all = args.all
    type_filter = args.type

    registry = PackageRegistry()
    state = PackageState()

    if show_all:
        # Show all available packages
        manifests = registry.discover()
        if type_filter:
            manifests = [m for m in manifests if m.package_type == type_filter]

        if not manifests:
            print("  No packages found.")
            return 0

        installed_names = {pkg.name for pkg in state.list_installed()}

        print(f"\n  Available Packages:")
        print(f"  {'Name':<35} {'Version':<10} {'Type':<12} {'Tier':<8} {'Status':<14} {'Installed'}")
        print(f"  {'─' * 35} {'─' * 10} {'─' * 12} {'─' * 8} {'─' * 14} {'─' * 9}")

        for m in manifests:
            inst = "✅" if m.package_name in installed_names else "  "
            print(f"  {m.package_name:<35} {m.package_version:<10} {m.package_type:<12} {m.tier:<8} {m.status:<14} {inst}")

        print(f"\n  Total: {len(manifests)} packages")

    else:
        # Show installed packages only
        installed = state.list_installed()
        if type_filter:
            # Filter by type using registry info
            filtered = []
            for pkg in installed:
                m = registry.get(pkg.name)
                if m and m.package_type == type_filter:
                    filtered.append(pkg)
            installed = filtered

        if not installed:
            print("  No packages installed.")
            print("  Use 'vit list --all' to see available packages.")
            print("  Use 'vit install <package>' to install one.")
            return 0

        print(f"\n  Installed Packages:")
        print(f"  {'Name':<35} {'Version':<10} {'Status':<10} {'Ports'}")
        print(f"  {'─' * 35} {'─' * 10} {'─' * 10} {'─' * 15}")

        for pkg in installed:
            ports = ", ".join(pkg.ports) if pkg.ports else "-"
            print(f"  {pkg.name:<35} {pkg.version:<10} {pkg.status:<10} {ports}")

        print(f"\n  Total: {len(installed)} packages")

    return 0


def register_list_command(subparsers: argparse._SubParsersAction):
    """Register 'vit list' subcommand."""
    parser = subparsers.add_parser(
        "list",
        help="List installed or available packages",
        description="Show installed packages, or all available packages with --all.",
    )
    parser.add_argument("--all", "-a", action="store_true", help="Show all available packages (not just installed)")
    parser.add_argument("--type", "-t", choices=["service", "order", "vertical", "extension"], help="Filter by package type")
    parser.set_defaults(func=cmd_list)
