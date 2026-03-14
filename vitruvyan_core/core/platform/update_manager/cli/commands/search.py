"""
vit search <query> — Search available packages (local + remote)

Usage:
    vit search llm
    vit search engine
    vit search finance --type vertical
    vit search frontier --remote
"""

import argparse

from vitruvyan_core.core.platform.package_manager.registry import PackageRegistry
from vitruvyan_core.core.platform.package_manager.state import PackageState


def cmd_search(args: argparse.Namespace) -> int:
    """Search for packages."""
    query = args.query
    type_filter = args.type
    include_remote = args.remote

    registry = PackageRegistry()
    state = PackageState()

    results = registry.search(query)
    if type_filter:
        results = [m for m in results if m.package_type == type_filter]

    installed_names = {pkg.name for pkg in state.list_installed()}

    # Collect remote results
    remote_results = []
    if include_remote:
        try:
            from vitruvyan_core.core.platform.package_manager.remote import RemoteRegistry
            remote = RemoteRegistry()
            remote_pkgs = remote.search(query)
            if type_filter:
                remote_pkgs = [p for p in remote_pkgs if p.get("type") == type_filter]
            # Exclude packages already found locally
            local_names = {m.package_name for m in results}
            remote_results = [p for p in remote_pkgs if p["name"] not in local_names]
        except Exception as e:
            print(f"  (remote search unavailable: {e})")

    if not results and not remote_results:
        print(f"  No packages matching '{query}'.")
        if not include_remote:
            print(f"  Try 'vit search {query} --remote' to search the remote registry.")
        return 0

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

    for pkg in remote_results:
        tier_label = "PREM" if pkg.get("license_required") else "    "
        latest = pkg.get("latest", "?")
        print(f"  {tier_label} {pkg['name']} v{latest} [remote]")
        print(f"        {pkg.get('description', '')}")
        print()

    total = len(results) + len(remote_results)
    print(f"  {total} package(s) found.")
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
    parser.add_argument("--remote", "-r", action="store_true", help="Also search remote registry")
    parser.set_defaults(func=cmd_search)
