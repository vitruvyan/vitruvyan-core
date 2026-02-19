"""
vit upgrade command - Apply Core upgrade with rollback on failure

Interactive confirmation + progress indicators.
"""

import argparse
import logging
import sys

from ...engine.registry import ReleaseRegistry, NetworkError
from ...engine.compatibility import CompatibilityChecker
from ...engine.planner import UpgradePlanner, PrerequisiteError
from ...engine.executor import UpgradeExecutor
from .update import get_current_version, find_vertical_manifest

logger = logging.getLogger(__name__)


def cmd_upgrade(args: argparse.Namespace) -> int:
    """
    Execute 'vit upgrade' command.
    
    Args:
        args: Parsed CLI arguments (--yes, --target, --channel)
    
    Returns:
        Exit code (0 = success, 1 = error/rollback)
    """
    channel = args.channel
    target_version = args.target
    non_interactive = args.yes
    
    print(f"🚀 Vitruvyan Core Upgrade (channel: {channel})\n")
    
    # Step 1: Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    # Step 2: Fetch target release
    try:
        registry = ReleaseRegistry()
        
        if target_version:
            # Specific version requested
            all_releases = registry.fetch_all(channel=channel)
            target_release = next(
                (r for r in all_releases if r.version == target_version),
                None
            )
            if not target_release:
                print(f"\n❌ Version {target_version} not found in {channel} channel")
                return 1
        else:
            # Latest version
            target_release = registry.fetch_latest(channel=channel)
        
        if not target_release:
            print(f"\n❌ No {channel} releases available")
            return 1
        
        print(f"Target version: {target_release.version}")
        print(f"Released: {target_release.release_date}\n")
    
    except NetworkError as e:
        print(f"\n❌ Network error: {e}")
        return 1
    
    # Step 3: Check if already on target version
    if current_version == target_release.version:
        print(f"✅ Already on {target_release.version}")
        return 0
    
    # Step 4: Find vertical manifest (for compatibility + smoke tests)
    manifest_dict = find_vertical_manifest()
    manifest_path = None
    
    if manifest_dict:
        # Find manifest file path
        import os
        cwd = os.getcwd()
        while cwd != "/":
            candidate = os.path.join(cwd, "vertical_manifest.yaml")
            if os.path.exists(candidate):
                manifest_path = candidate
                break
            parent = os.path.dirname(cwd)
            if parent == cwd:
                break
            cwd = parent
    
    # Step 5: Compatibility check
    if manifest_dict:
        print("📋 Checking compatibility...")
        checker = CompatibilityChecker()
        result = checker.check(current_version, target_release.version, manifest_dict)
        
        if not result.compatible:
            print(f"\n❌ Incompatible: {result.blocking_reason}")
            print("   Update vertical manifest or choose different version")
            return 1
        
        print(f"✅ Compatible with vertical constraints\n")
    
    # Step 6: Generate upgrade plan
    print("📝 Generating upgrade plan...")
    planner = UpgradePlanner()
    
    try:
        plan = planner.plan(
            from_version=current_version,
            to_version=target_release.version,
            release=target_release,
            manifest_path=manifest_path
        )
    except PrerequisiteError as e:
        print(f"\n❌ Prerequisites failed:\n")
        print(f"{e}\n")
        return 1
    
    # Step 7: Show plan
    print(f"\n{'='*60}")
    print(f"  UPGRADE PLAN")
    print(f"{'='*60}")
    print(f"From: {plan.from_version}")
    print(f"To:   {plan.to_version}")
    print(f"Estimated downtime: ~{plan.estimated_downtime}s")
    print(f"Rollback strategy: {plan.rollback_strategy}")
    print()
    
    # Show changes
    if plan.changes:
        breaking = plan.changes.get("breaking", [])
        features = plan.changes.get("features", [])
        fixes = plan.changes.get("fixes", [])
        
        if breaking:
            print(f"⚠️  BREAKING CHANGES ({len(breaking)}):")
            for change in breaking:
                print(f"   - {change}")
            print()
        
        if features:
            print(f"✨ NEW FEATURES ({len(features)}):")
            for change in features:
                print(f"   - {change}")
            print()
        
        if fixes:
            print(f"🐛 BUG FIXES ({len(fixes)}):")
            for change in fixes:
                print(f"   - {change}")
            print()
    
    # Show smoke tests
    if plan.tests_required:
        print(f"🧪 Smoke tests to run:")
        for test in plan.tests_required:
            print(f"   - {test}")
        print()
    else:
        print(f"⚠️  No smoke tests configured (risky upgrade)\n")
    
    print(f"{'='*60}\n")
    
    # Step 8: Confirmation (unless --yes)
    if not non_interactive:
        response = input("Proceed with upgrade? [y/N]: ").strip().lower()
        if response != "y":
            print("Upgrade cancelled")
            return 0
        print()
    
    # Step 9: Execute upgrade
    print("🔧 Executing upgrade...\n")
    
    executor = UpgradeExecutor()
    success = executor.apply(plan, manifest_path=manifest_path)
    
    if success:
        print(f"\n✅ Upgrade completed successfully!")
        print(f"   Current version: {plan.to_version}")
        print(f"   Snapshot tag: {executor.last_snapshot_tag}")
        print(f"\n💡 To rollback:")
        print(f"   vit rollback")
        return 0
    else:
        print(f"\n❌ Upgrade failed (rollback completed)")
        print(f"   Current version: {plan.from_version}")
        print(f"\n💡 Check logs for details:")
        print(f"   Likely cause: Smoke tests failed")
        return 1


def register_upgrade_command(subparsers):
    """
    Register 'vit upgrade' subcommand.
    
    Args:
        subparsers: argparse subparsers object
    """
    parser = subparsers.add_parser(
        "upgrade",
        help="Apply Core upgrade (with smoke tests + rollback)",
        description="Apply Core upgrade with compatibility validation and automatic rollback on failure"
    )
    
    parser.add_argument(
        "--channel",
        choices=["stable", "beta"],
        default="stable",
        help="Release channel (default: stable)"
    )
    
    parser.add_argument(
        "--target",
        help="Target version (default: latest)"
    )
    
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Non-interactive mode (skip confirmation)"
    )
    
    parser.set_defaults(func=cmd_upgrade)
