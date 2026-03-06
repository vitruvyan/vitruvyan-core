"""
vit update command - Check for Core updates (read-only)

Shows current version + latest available for selected channel.
"""

import argparse
import json
import logging
import os

from ...engine.registry import ReleaseRegistry, NetworkError
from ...engine.compatibility import CompatibilityChecker
from ..channel_state import get_default_channel

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
    channel = args.channel or get_default_channel()
    json_mode = bool(getattr(args, "json", False))

    def out(message: str = "") -> None:
        if not json_mode:
            print(message)

    status = {
        "status": "ok",
        "channel": channel,
        "current_version": None,
        "latest_version": None,
        "update_available": False,
        "compatible": None,
        "reason": None,
        "changes": {},
        "migration_guide_url": None,
    }

    out(f"🔍 Checking for Core updates (channel: {channel})...\n")

    current_version = get_current_version()
    status["current_version"] = current_version
    out(f"Current Core version: {current_version}")

    try:
        registry = ReleaseRegistry()
        latest = registry.fetch_latest(channel=channel)

        if not latest:
            status["status"] = "error"
            status["reason"] = f"No {channel} releases found on GitHub"
            if json_mode:
                print(json.dumps(status, indent=2))
            else:
                out(f"\n❌ {status['reason']}.")
                out("   Repository may be private or network unavailable.")
            return 1

        status["latest_version"] = latest.version
        status["changes"] = latest.changes or {}
        status["migration_guide_url"] = latest.migration_guide_url
        out(f"Latest {channel} version: {latest.version}")
        out(f"Released: {latest.release_date}")

    except NetworkError as e:
        status["status"] = "error"
        status["reason"] = f"Network error: {e}"
        if json_mode:
            print(json.dumps(status, indent=2))
        else:
            out(f"\n❌ {status['reason']}")
            out("   Check your internet connection and try again.")
        return 2

    if current_version == "unknown":
        out("\n⚠️  Current version unknown (cannot compare)")
    elif current_version == latest.version:
        out(f"\n✅ You are on the latest {channel} version!")
    else:
        current_tuple = CompatibilityChecker().parse_semver(current_version)
        latest_tuple = CompatibilityChecker().parse_semver(latest.version)

        if latest_tuple > current_tuple:
            status["update_available"] = True
            out(f"\n🆕 New version available: {current_version} → {latest.version}")
        else:
            out(f"\n⚠️  You are on a newer version than latest {channel}")

    manifest = find_vertical_manifest()
    if manifest:
        out("\n📋 Checking compatibility with vertical manifest...")

        checker = CompatibilityChecker()
        result = checker.check(
            current_version=current_version,
            target_version=latest.version,
            manifest=manifest
        )
        status["compatible"] = result.compatible
        if not result.compatible:
            status["reason"] = result.blocking_reason

        if result.compatible:
            min_version = manifest.get("compatibility", {}).get("min_core_version", "any")
            max_version = manifest.get("compatibility", {}).get("max_core_version", "any")
            out("✅ Compatible with vertical constraints")
            out(f"   Vertical supports: {min_version} - {max_version}")
        else:
            out(f"❌ Incompatible: {result.blocking_reason}")
            out(f"   Update vertical manifest to support {latest.version}")

    if latest.changes:
        out(f"\n📝 Changes in {latest.version}:")

        breaking = latest.changes.get("breaking", [])
        if breaking:
            out("   ⚠️  BREAKING:")
            for change in breaking:
                out(f"      - {change}")

        features = latest.changes.get("features", [])
        if features:
            out("   ✨ Features:")
            for change in features:
                out(f"      - {change}")

        fixes = latest.changes.get("fixes", [])
        if fixes:
            out("   🐛 Fixes:")
            for change in fixes:
                out(f"      - {change}")

    if latest.migration_guide_url:
        out(f"\n📖 Migration guide: {latest.migration_guide_url}")

    if json_mode:
        print(json.dumps(status, indent=2))
    else:
        out("\n💡 To upgrade:")
        out(f"   vit upgrade --channel {channel}")

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
        default=None,
        help="Release channel (default: persisted channel or stable)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    
    parser.set_defaults(func=cmd_update)
