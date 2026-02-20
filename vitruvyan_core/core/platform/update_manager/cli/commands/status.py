"""
vit status command - Show update status and notification state

Displays:
- Current Core version
- Latest available version (if check succeeds)
- Update availability
- Last update check time
- Notification configuration
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from typing import Optional

from ...engine.compatibility import CompatibilityChecker
from ...engine.models import Release
from ...engine.registry import NetworkError, ReleaseRegistry
from ...notifications.config import (
    NotificationChannel,
    get_last_check_time,
    load_notification_config,
)
from ..formatters import format_release_info

logger = logging.getLogger(__name__)


def format_last_check(timestamp: Optional[float]) -> str:
    """Format last check timestamp as human-readable string."""
    if timestamp is None:
        return "Never"
    
    dt = datetime.fromtimestamp(timestamp)
    now = datetime.now()
    delta = now - dt
    
    if delta.total_seconds() < 3600:
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif delta.total_seconds() < 86400:
        hours = int(delta.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = delta.days
        return f"{days} day{'s' if days != 1 else ''} ago"


def get_current_version() -> str:
    """Get current Core version (same strategy as update.py)."""
    try:
        from vitruvyan_core import __version__
        return __version__
    except (ImportError, AttributeError):
        pass
    
    try:
        import subprocess
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return result.stdout.strip().lstrip("v")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return "unknown"


def find_vertical_manifest() -> Optional[str]:
    """Find vertical_manifest.yaml in current directory or parents."""
    import os
    
    current = os.getcwd()
    while current != "/":
        manifest_path = os.path.join(current, "vertical_manifest.yaml")
        if os.path.exists(manifest_path):
            return manifest_path
        
        if os.path.exists(os.path.join(current, ".git")):
            break
        
        current = os.path.dirname(current)
    
    return None


def run(args: argparse.Namespace) -> int:
    """
    Execute vit status command.
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        Exit code (0 = ok, 1 = error, 2 = update available)
    """
    # Get current version
    current_version = get_current_version()
    
    # Load notification config
    manifest_path = find_vertical_manifest()
    config = load_notification_config(manifest_path)
    
    # Get last check time
    last_check = get_last_check_time()
    
    # Build status dict
    status = {
        "current_version": current_version,
        "latest_version": None,
        "update_available": False,
        "breaking_changes": False,
        "last_check": last_check,
        "last_check_human": format_last_check(last_check),
        "notifications": {
            "enabled": config.enabled,
            "channels": [ch.value for ch in config.channels],
            "check_interval_hours": config.check_interval_hours,
        },
        "manifest_found": manifest_path is not None,
    }
    
    # Try fetching latest release (network call)
    try:
        registry = ReleaseRegistry()
        channel = args.channel if hasattr(args, "channel") else "stable"
        latest_release = registry.fetch_latest(channel=channel)
        
        if latest_release is None:
            status["latest_version"] = "unknown"
            status["update_available"] = False
            status["warning"] = f"No {channel} releases found on GitHub"
        else:
            latest_version_normalized = latest_release.version.lstrip("v")
            current_version_normalized = current_version.lstrip("v")
            
            status["latest_version"] = latest_release.version
            status["update_available"] = latest_version_normalized != current_version_normalized
            status["breaking_changes"] = len(latest_release.changes.get("breaking", [])) > 0
            status["changelog_url"] = f"https://github.com/dbaldoni/vitruvyan-core/releases/tag/{latest_release.version}"
            
            # Check compatibility if manifest present
            if manifest_path and status["update_available"]:
                checker = CompatibilityChecker()
                import yaml
                with open(manifest_path, "r") as f:
                    manifest = yaml.safe_load(f)
                
                result = checker.check(
                    current_version=current_version,
                    target_version=latest_release.version,
                    manifest=manifest,
                )
                status["compatible"] = result.compatible
                if not result.compatible:
                    status["compatibility_issues"] = result.issues
    
    except NetworkError as e:
        logger.warning(f"Network error fetching latest release: {e}")
        status["error"] = "Network error - cannot check for updates"
    except Exception as e:
        logger.error(f"Error checking for updates: {e}", exc_info=True)
        status["error"] = str(e)
    
    # Output format
    if args.json:
        print(json.dumps(status, indent=2))
    else:
        _print_status_human(status)
    
    # Exit code
    if "error" in status:
        return 1
    elif status["update_available"]:
        return 2  # Update available (can be used in scripts)
    else:
        return 0


def _print_status_human(status: dict) -> None:
    """Print status in human-readable format."""
    print("─" * 60)
    print("  Vitruvyan Core — Update Status")
    print("─" * 60)
    print()
    
    # Version info
    print(f"  Current version:  {status['current_version']}")
    if status.get("latest_version"):
        print(f"  Latest version:   {status['latest_version']}")
    
    # Update availability
    if status.get("update_available"):
        if status.get("breaking_changes"):
            print("\n  ⚠️  Update available (BREAKING CHANGES)")
        else:
            print("\n  ✨ Update available")
        
        if status.get("changelog_url"):
            print(f"  Changelog: {status['changelog_url']}")
        
        # Compatibility
        if "compatible" in status:
            if status["compatible"]:
                print("  ✅ Compatible with current manifest")
            else:
                print("  ❌ Incompatible with current manifest")
                if "compatibility_issues" in status:
                    print("\n  Issues:")
                    for issue in status["compatibility_issues"]:
                        print(f"    - {issue}")
    elif status.get("latest_version"):
        print("\n  ✅ Up to date")
    
    # Error handling
    if "error" in status:
        print(f"\n  ⚠️  Error: {status['error']}")
    
    # Warning handling
    if "warning" in status:
        print(f"\n  ℹ️  {status['warning']}")
    
    # Notification status
    print("\n  Notification settings:")
    if status["notifications"]["enabled"]:
        print(f"    Status: Enabled")
        channels_str = ", ".join(status["notifications"]["channels"])
        print(f"    Channels: {channels_str}")
        print(f"    Check interval: {status['notifications']['check_interval_hours']}h")
    else:
        print("    Status: Disabled")
    
    print(f"\n  Last check: {status['last_check_human']}")
    
    if not status["manifest_found"]:
        print("\n  ℹ️  No vertical_manifest.yaml found (running outside vertical)")
    
    print()
    print("─" * 60)


def register_status_command(subparsers) -> None:
    """Register status command with argparse."""
    parser = subparsers.add_parser(
        "status",
        help="Show update status and notification state",
        description="Display current version, available updates, and notification configuration",
    )
    
    parser.add_argument(
        "--channel",
        choices=["stable", "beta", "dev"],
        default="stable",
        help="Release channel to check (default: stable)",
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )
    
    parser.set_defaults(func=run)
