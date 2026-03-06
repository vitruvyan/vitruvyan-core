"""
vit plan command - Show upgrade plan without applying

Displays changes, risks, smoke tests, downtime estimate.
"""

import argparse
import logging

from ...engine.registry import ReleaseRegistry, NetworkError
from ...engine.compatibility import CompatibilityChecker
from ...engine.planner import UpgradePlanner, PrerequisiteError
from .update import get_current_version, find_vertical_manifest
from ..channel_state import get_default_channel

logger = logging.getLogger(__name__)


def cmd_plan(args: argparse.Namespace) -> int:
    """
    Execute 'vit plan' command.
    
    Args:
        args: Parsed CLI arguments (--target, --channel)
    
    Returns:
        Exit code (0 = success, 1 = error)
    """
    channel = args.channel or get_default_channel()
    target_version = args.target
    
    print(f"📋 Vitruvyan Core Upgrade Plan\n")
    
    # Step 1: Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    # Step 2: Fetch target release
    try:
        registry = ReleaseRegistry()
        if target_version:
            all_releases = registry.fetch_all(channel=channel)
            target_release = next(
                (r for r in all_releases if r.version == target_version),
                None
            )
            if not target_release:
                print(f"\n❌ Version {target_version} not found in {channel} channel")
                return 1
        else:
            target_release = registry.fetch_latest(channel=channel)
            if not target_release:
                print(f"\n❌ No {channel} releases available")
                return 1
            target_version = target_release.version

        print(f"Target version: {target_version}\n")
    
    except NetworkError as e:
        print(f"\n❌ Network error: {e}")
        return 1
    
    # Step 3: Find vertical manifest
    manifest_dict = find_vertical_manifest()
    manifest_path = None
    
    if manifest_dict:
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
    
    # Step 4: Compatibility check
    if manifest_dict:
        checker = CompatibilityChecker()
        result = checker.check(current_version, target_version, manifest_dict)
        
        if not result.compatible:
            print(f"❌ INCOMPATIBLE: {result.blocking_reason}\n")
            return 1
        
        print(f"✅ Compatible with vertical constraints\n")
    
    # Step 5: Generate plan
    planner = UpgradePlanner()
    
    try:
        plan = planner.plan(
            from_version=current_version,
            to_version=target_version,
            release=target_release,
            manifest_path=manifest_path
        )
    except PrerequisiteError as e:
        print(f"❌ Prerequisites failed:\n{e}\n")
        return 1
    
    # Step 6: Display plan
    print(f"{'='*60}")
    print(f"  UPGRADE PLAN: {plan.from_version} → {plan.to_version}")
    print(f"{'='*60}\n")
    
    # Timeline
    print(f"⏱️  TIMELINE")
    print(f"   Estimated downtime: ~{plan.estimated_downtime}s")
    print(f"   Rollback strategy: {plan.rollback_strategy}")
    print()
    
    # Changes
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
            for change in features[:5]:  # Limit to 5
                print(f"   - {change}")
            if len(features) > 5:
                print(f"   ... and {len(features) - 5} more")
            print()
        
        if fixes:
            print(f"🐛 BUG FIXES ({len(fixes)}):")
            for change in fixes[:5]:  # Limit to 5
                print(f"   - {change}")
            if len(fixes) > 5:
                print(f"   ... and {len(fixes) - 5} more")
            print()
    
    # Smoke tests
    print(f"🧪 SMOKE TESTS")
    if plan.tests_required:
        for test in plan.tests_required:
            print(f"   ✓ {test}")
    else:
        print(f"   ⚠️  No smoke tests configured (risky upgrade)")
    print()
    
    # Risk assessment
    print(f"⚡ RISK ASSESSMENT")
    has_breaking = len(plan.changes.get("breaking", [])) > 0
    has_tests = len(plan.tests_required) > 0
    
    if has_breaking and not has_tests:
        risk_level = "HIGH"
        risk_color = "⚠️"
    elif has_breaking and has_tests:
        risk_level = "MEDIUM"
        risk_color = "⚡"
    elif not has_breaking and has_tests:
        risk_level = "LOW"
        risk_color = "✅"
    else:
        risk_level = "MEDIUM"
        risk_color = "⚡"
    
    print(f"   {risk_color} Risk level: {risk_level}")
    
    if has_breaking:
        print(f"   ⚠️  Breaking changes require manual migration")
    if not has_tests:
        print(f"   ⚠️  No automated validation (smoke tests missing)")
    
    print()
    print(f"{'='*60}\n")
    
    # Next steps
    print(f"💡 To apply this upgrade:")
    print(f"   vit upgrade --target {target_version} --channel {channel}")
    print()
    
    return 0


def register_plan_command(subparsers):
    """
    Register 'vit plan' subcommand.
    
    Args:
        subparsers: argparse subparsers object
    """
    parser = subparsers.add_parser(
        "plan",
        help="Show upgrade plan without applying",
        description="Generate and display upgrade plan (changes, risks, tests, downtime)"
    )
    
    parser.add_argument(
        "--target",
        help="Target version (e.g., 1.2.0)"
    )
    
    parser.add_argument(
        "--channel",
        choices=["stable", "beta"],
        default=None,
        help="Release channel (default: persisted channel or stable)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Reserved for machine-readable output (human output currently default)"
    )
    
    parser.set_defaults(func=cmd_plan)
