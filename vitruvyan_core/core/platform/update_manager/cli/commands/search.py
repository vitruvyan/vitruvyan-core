"""
vit search <query> — Search available packages

Usage:
    vit search llm
    vit search engine
    vit search finance --type vertical
"""

import argparse

from vitruvyan_core.core.platform.package_manager.registry import PackageRegistry
from vitruvyan_core.core.platform.package_manager.state import PackageState


def cmd_search(args: argparse.Namespace) -> int:
    """Search for packages."""
    query = args.query
    type_filter = args.type

    registry = PackageRegistry()
    state = PackageState()

    results = registry.search(query)
    if type_filter:
        results = [m for m in results if m.package_type == type_filter]

    if not results:
        print(f"  No packages matching '{query}'.")
        return 0

    installed_names = {pkg.name for pkg in state.list_installed()}

    print(f"\n  Search results for '{query}':")
    print()

    for m in results:
        inst = " [installed]" if m.package_name in installed_names else ""
        tier_label = "CORE" if m.tier == "core" else "    "
        print(f"  {tier_label} {m.package_name} v{m.package_version} ({m.status}){inst}")
        print(f"        {m.description}")
        if m.ports:
            print(f"        Ports: {', '.join(m.ports)}")
        print()

    print(f"  {len(results)} package(s) found.")
    return 0


def register_search_command(subparsers: argparse._SubParsersAction):
    """Register 'vit search' subcommand."""
    parser = subparsers.add_parser(
        "search",
        help="Search available packages",
        description="Search for packages by name or description.",
    )
    parser.add_argument("query", help="Search query (matches name and description)")
    parser.add_argument("--type", "-t", choices=["service", "order", "vertical", "extension"], help="Filter by package type")
    parser.set_defaults(func=cmd_search)
