"""
vit remove <package> — Remove an installed .vit package

Usage:
    vit remove neural_engine
    vit remove mcp --purge
    vit remove neural_engine --yes
"""

import argparse

from vitruvyan_core.core.platform.package_manager.registry import PackageRegistry
from vitruvyan_core.core.platform.package_manager.installer import PackageInstaller
from vitruvyan_core.core.platform.package_manager.state import PackageState


def cmd_remove(args: argparse.Namespace) -> int:
    """Execute package removal."""
    package_name = args.package
    purge = args.purge
    skip_confirm = args.yes

    registry = PackageRegistry()
    state = PackageState()
    installer = PackageInstaller(state)

    # Find manifest
    manifest = registry.get(package_name)
    if not manifest:
        print(f"  Package '{package_name}' not found in registry.")
        return 1

    # Check if installed
    if not state.is_installed(manifest.package_name):
        print(f"  {manifest.package_name} is not installed.")
        return 0

    # Core tier — warn
    if manifest.tier == "core":
        print(f"  {manifest.package_name} is a core component.")
        print(f"  Removing core components is not recommended.")
        return 1

    # Check dependents
    installed = state.list_installed()
    dependents = []
    for pkg in installed:
        m = registry.get(pkg.name)
        if m:
            for dep_spec in m.required_deps:
                dep_name = dep_spec.split(">=")[0].split("==")[0].split("<=")[0].strip()
                if dep_name == manifest.package_name:
                    dependents.append(pkg.name)

    if dependents:
        print(f"  Cannot remove {manifest.package_name}: required by {', '.join(dependents)}")
        print(f"  Remove dependents first: vit remove {' '.join(dependents)}")
        return 1

    # Confirm
    existing = state.get(manifest.package_name)
    print(f"\n  Package: {manifest.package_name} v{existing.version}")
    if purge:
        print(f"  Mode:    PURGE (data and volumes will be deleted)")
    else:
        print(f"  Mode:    Remove (data preserved)")

    if not skip_confirm:
        print()
        answer = input("  Proceed with removal? [y/N] ").strip().lower()
        if answer != "y":
            print("  Removal cancelled.")
            return 0

    # Remove
    print(f"\n  Removing {manifest.package_name}...")
    success = installer.remove(manifest, purge=purge)
    if success:
        print(f"  {manifest.package_name} removed.")
    else:
        print(f"  Failed to remove {manifest.package_name}.")
        return 2

    return 0


def register_remove_command(subparsers: argparse._SubParsersAction):
    """Register 'vit remove' subcommand."""
    parser = subparsers.add_parser(
        "remove",
        help="Remove an installed package",
        description="Remove a .vit package and optionally purge its data.",
    )
    parser.add_argument("package", help="Package name to remove")
    parser.add_argument("--purge", action="store_true", help="Also delete data and volumes")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    parser.set_defaults(func=cmd_remove)
