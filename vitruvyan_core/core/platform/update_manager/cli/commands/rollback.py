"""
vit rollback command - Revert to previous Core version

Restores last snapshot from upgrade history.
"""

import argparse
import logging

from ...engine.executor import UpgradeExecutor

logger = logging.getLogger(__name__)


def cmd_rollback(args: argparse.Namespace) -> int:
    """
    Execute 'vit rollback' command.
    
    Args:
        args: Parsed CLI arguments
    
    Returns:
        Exit code (0 = success, 1 = error)
    """
    print("🔙 Vitruvyan Core Rollback\n")
    
    # Step 1: Initialize executor
    executor = UpgradeExecutor()
    
    # Step 2: Check for snapshot
    snapshot_tag = executor._get_last_snapshot_tag()
    
    if not snapshot_tag:
        print("❌ No snapshot found")
        print("   Rollback requires a previous upgrade with snapshot")
        print()
        print("💡 Snapshot tags created by:")
        print("   vit upgrade")
        print()
        return 1
    
    print(f"Snapshot found: {snapshot_tag}")
    
    # Step 3: Confirmation
    response = input(f"\nRevert to {snapshot_tag}? [y/N]: ").strip().lower()
    if response != "y":
        print("Rollback cancelled")
        return 0
    
    print()
    
    # Step 4: Execute rollback
    print("🔧 Rolling back...\n")
    
    success = executor.rollback()
    
    if success:
        print(f"✅ Rollback completed")
        print(f"   Restored: {snapshot_tag}")
        print()
        print("💡 Verify with:")
        print("   git describe --tags")
        print()
        return 0
    else:
        print(f"❌ Rollback failed")
        print("   Check logs for details")
        print()
        print("💡 Manual rollback:")
        print(f"   git checkout {snapshot_tag}")
        print()
        return 1


def register_rollback_command(subparsers):
    """
    Register 'vit rollback' subcommand.
    
    Args:
        subparsers: argparse subparsers object
    """
    parser = subparsers.add_parser(
        "rollback",
        help="Revert to previous Core version",
        description="Restore last snapshot from upgrade history (reverts failed upgrades)"
    )
    
    parser.set_defaults(func=cmd_rollback)
