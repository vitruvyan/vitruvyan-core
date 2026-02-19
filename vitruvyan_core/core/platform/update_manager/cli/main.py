"""
CLI Entry Point for `vit` Command

Usage:
    vit update
    vit upgrade
    vit plan --target v1.2.0
    vit rollback
    vit channel stable
    vit status

Phase 1: Implement `vit update` command
"""

import sys
import argparse


def cli_main():
    """
    Main entry point for `vit` CLI.
    
    Called by setup.py:
        [project.scripts]
        vit = "core.platform.update_manager.cli.main:cli_main"
    """
    parser = argparse.ArgumentParser(
        prog="vit",
        description="Vitruvyan Core Update Manager",
        epilog="Documentation: docs/contracts/platform/UPDATE_SYSTEM_CONTRACT_V1.md"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # vit update
    update_parser = subparsers.add_parser(
        "update",
        help="Check for updates (sync release registry)"
    )
    update_parser.add_argument("--json", action="store_true", help="JSON output")
    
    # vit upgrade
    upgrade_parser = subparsers.add_parser(
        "upgrade",
        help="Apply upgrade (with compatibility validation)"
    )
    upgrade_parser.add_argument("--yes", action="store_true", help="Non-interactive mode")
    upgrade_parser.add_argument("--target", help="Target version (default: latest)")
    
    # vit plan
    plan_parser = subparsers.add_parser(
        "plan",
        help="Show upgrade plan (changes, risks, tests)"
    )
    plan_parser.add_argument("--target", required=True, help="Target version")
    
    # vit rollback
    rollback_parser = subparsers.add_parser(
        "rollback",
        help="Revert to previous version"
    )
    
    # vit channel
    channel_parser = subparsers.add_parser(
        "channel",
        help="Switch update channel (stable|beta)"
    )
    channel_parser.add_argument("channel", choices=["stable", "beta"])
    
    # vit status
    status_parser = subparsers.add_parser(
        "status",
        help="Show current version + available updates"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Phase 1: Only `update` implemented
    if args.command == "update":
        print("⚠️  Phase 1: `vit update` not yet implemented")
        print("See: docs/knowledge_base/development/core_update_upgrade_masterplan.md")
        sys.exit(0)
    else:
        print(f"⚠️  Command `vit {args.command}` not yet implemented (Phase 2+)")
        sys.exit(0)


if __name__ == "__main__":
    cli_main()
