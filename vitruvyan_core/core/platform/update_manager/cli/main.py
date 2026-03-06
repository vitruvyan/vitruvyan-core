"""
CLI Entry Point for `vit` Command

Usage:
    vit update
    vit upgrade
    vit plan --target v1.2.0
    vit rollback
    vit channel stable
    vit status
    vit release                 # create GitHub Release from current tag
    vit release --dry-run       # preview without API calls

Phase 2: upgrade, plan, rollback implemented
Phase 3: release command added
"""

import sys
import argparse
import logging

from .commands.update import register_update_command
from .commands.upgrade import register_upgrade_command
from .commands.plan import register_plan_command
from .commands.rollback import register_rollback_command
from .commands.status import register_status_command
from .commands.completion import register_completion_command
from .commands.release import register_release_command
from .channel_state import set_default_channel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


def cmd_channel(args: argparse.Namespace) -> int:
    """Persist default channel selection for future runs."""
    channel = args.channel
    set_default_channel(channel)
    print(f"✅ Default channel set to: {channel}")
    return 0


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
    
    # Register commands (Phase 2+: update, upgrade, plan, rollback, status, release)
    register_update_command(subparsers)
    register_upgrade_command(subparsers)
    register_plan_command(subparsers)
    register_rollback_command(subparsers)
    register_status_command(subparsers)
    register_completion_command(subparsers)
    register_release_command(subparsers)
    
    # vit channel
    channel_parser = subparsers.add_parser(
        "channel",
        help="Switch update channel (stable|beta)"
    )
    channel_parser.add_argument("channel", choices=["stable", "beta"])
    channel_parser.set_defaults(func=cmd_channel)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command (if func is registered)
    if hasattr(args, "func"):
        exit_code = args.func(args)
        sys.exit(exit_code)
    else:
        # Command not yet implemented
        print(f"⚠️  Command `vit {args.command}` not yet implemented (Phase 2+)")
        sys.exit(0)


if __name__ == "__main__":
    cli_main()
