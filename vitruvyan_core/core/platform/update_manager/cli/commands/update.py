"""
vit update command - Check for Core updates (read-only)

Shows current version + latest available for selected channel.
"""

import argparse
import logging
import os
import sys

from ...engine.registry import ReleaseRegistry, NetworkError
from ...engine.compatibility import CompatibilityChecker
from ..formatters import format_release_info, format_compatibility_result

logger = logging.getLogger(__name__)


def get_current_version() -> str:
    """
    Get current Core version.
    
    Strategy:
    1. Try reading vitruvyan_core.__version__
    2. Fallback: git describe --tags
    3. Fallback: "unknown"
    
    Returns:
        Version string (e.g., "1.0.0")
    """
    # Strategy 1: Read __version__ from package
    try:
        from vitruvyan_core import __version__
        return __version__
    except (ImportError, AttributeError):
        pass
    
    # Strategy 2: Git describe
    try:
        import subprocess
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        version = result.stdout.strip().lstrip("v")
        return version
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Strategy 3: Fallback
    return "unknown"


def find_vertical_manifest() -> dict:
    """
    Find vertical_manifest.yaml in current directory or parents.
    
    Returns:
        Manifest dict or empty dict if not found
    """
    import yaml
    
    # Walk up from current directory to Git repo root
    current = os.getcwd()
    while current != "/":
        manifest_path = os.path.join(current, "vertical_manifest.yaml")
        if os.path.exists(manifest_path):
            logger.info(f"Found vertical manifest: {manifest_path}")
            with open(manifest_path, "r") as f:
                return yaml.safe_load(f)
        
        # Check if Git repo root
        if os.path.exists(os.path.join(current, ".git")):
            logger.debug("Reached Git repo root, no manifest found")
            break
        
        # Move up one directory
        parent = os.path.dirname(current)
        if parent == current:
            break  # Reached filesystem root
        current = parent
    
    logger.debug("No vertical manifest found")
    return {}


def cmd_update(args: argparse.Namespace) -> int:
    """
    Execute 'vit update' command.
    
    Args:
        args: Parsed CLI arguments (channel, etc.)
    
    Returns:
        Exit code (0 = success, 1 = error)
    """
    channel = args.channel
    
    print(f"🔍 Checking for Core updates (channel: {channel})...\n")
    
    # Get current version
    current_version = get_current_version()
    print(f"Current Core version: {current_version}")
    
    # Fetch latest release
    try:
        registry = ReleaseRegistry()
        latest = registry.fetch_latest(channel=channel)
        
        if not latest:
            print(f"\n❌ No {channel} releases found on GitHub.")
            print("   Repository may be private or network unavailable.")
            return 1
        
        print(f"Latest {channel} version: {latest.version}")
        print(f"Released: {latest.release_date}")
        
    except NetworkError as e:
        print(f"\n❌ Network error: {e}")
        print("   Check your internet connection and try again.")
        return 1
    
    # Compare versions
    if current_version == "unknown":
        print("\n⚠️  Current version unknown (cannot compare)")
    elif current_version == latest.version:
        print(f"\n✅ You are on the latest {channel} version!")
    else:
        current_tuple = CompatibilityChecker().parse_semver(current_version)
        latest_tuple = CompatibilityChecker().parse_semver(latest.version)
        
        if latest_tuple > current_tuple:
            print(f"\n🆕 New version available: {current_version} → {latest.version}")
        else:
            print(f"\n⚠️  You are on a newer version than latest {channel}")
    
    # Check compatibility with vertical manifest (if found)
    manifest = find_vertical_manifest()
    if manifest:
        print(f"\n📋 Checking compatibility with vertical manifest...")
        
        checker = CompatibilityChecker()
        result = checker.check(
            current_version=current_version,
            target_version=latest.version,
            manifest=manifest
        )
        
        if result.compatible:
            print(f"✅ Compatible with vertical constraints")
            min_version = manifest.get("compatibility", {}).get("min_core_version", "any")
            max_version = manifest.get("compatibility", {}).get("max_core_version", "any")
            print(f"   Vertical supports: {min_version} - {max_version}")
        else:
            print(f"❌ Incompatible: {result.blocking_reason}")
            print(f"   Update vertical manifest to support {latest.version}")
    
    # Show changes
    if latest.changes:
        print(f"\n📝 Changes in {latest.version}:")
        
        breaking = latest.changes.get("breaking", [])
        if breaking:
            print(f"   ⚠️  BREAKING:")
            for change in breaking:
                print(f"      - {change}")
        
        features = latest.changes.get("features", [])
        if features:
            print(f"   ✨ Features:")
            for change in features:
                print(f"      - {change}")
        
        fixes = latest.changes.get("fixes", [])
        if fixes:
            print(f"   🐛 Fixes:")
            for change in fixes:
                print(f"      - {change}")
    
    # Migration guide
    if latest.migration_guide_url:
        print(f"\n📖 Migration guide: {latest.migration_guide_url}")
    
    # Next steps
    print(f"\n💡 To upgrade:")
    print(f"   vit upgrade --channel {channel}")
    
    return 0


def register_update_command(subparsers):
    """
    Register 'vit update' subcommand.
    
    Args:
        subparsers: argparse subparsers object
    """
    parser = subparsers.add_parser(
        "update",
        help="Check for Core updates (read-only)",
        description="Check for available Core updates on GitHub Releases"
    )
    
    parser.add_argument(
        "--channel",
        choices=["stable", "beta"],
        default="stable",
        help="Release channel (default: stable)"
    )
    
    parser.set_defaults(func=cmd_update)
