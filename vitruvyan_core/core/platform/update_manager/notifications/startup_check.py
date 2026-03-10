"""
Startup check — Check for updates on system boot/service startup.

Usage:
    from core.platform.update_manager.notifications import startup_check
    
    # Call this in service startup (e.g., api_graph/__init__.py)
    startup_check()
"""

import time
from typing import Optional

from .config import (
    NotificationChannel,
    NotificationConfig,
    get_last_check_time,
    load_notification_config,
    set_last_check_time,
)
from .notifiers import (
    DesktopNotifier,
    LogNotifier,
    UpdateNotification,
    WebhookNotifier,
)
from ..engine.compatibility import CompatibilityChecker
from ..engine.registry import ReleaseRegistry


def _get_current_version() -> str:
    """Best-effort current Core version detection."""
    try:
        from vitruvyan_core import __version__

        return __version__
    except Exception:
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
    except Exception:
        return "unknown"


def _extract_breaking_changes(release_obj) -> list[str]:
    """Normalize breaking changes from legacy/new release shapes."""
    # Legacy mocks/tests may provide `breaking_changes` directly.
    legacy = getattr(release_obj, "breaking_changes", None)
    if isinstance(legacy, list):
        return legacy
    if isinstance(legacy, bool):
        return ["Breaking changes present"] if legacy else []

    changes = getattr(release_obj, "changes", {}) or {}
    if isinstance(changes, dict):
        breaking = changes.get("breaking", [])
        return breaking if isinstance(breaking, list) else []
    return []


def should_check_updates(config: NotificationConfig) -> bool:
    """
    Determine if update check should run.
    
    Args:
        config: Notification configuration
    
    Returns:
        True if update check should run
    """
    if not config.enabled:
        return False
    
    if not config.check_on_startup:
        return False
    
    # Check if enough time has passed since last check
    last_check = get_last_check_time()
    if last_check is None:
        return True  # Never checked before
    
    hours_since_check = (time.time() - last_check) / 3600
    return hours_since_check >= config.check_interval_hours


def startup_check(manifest_path: Optional[str] = None, force: bool = False) -> None:
    """
    Check for Core updates on system startup.
    
    Args:
        manifest_path: Path to vertical_manifest.yaml (optional)
        force: Force check even if interval not elapsed
    """
    # Load notification config
    config = load_notification_config(manifest_path)
    
    # Check if we should run
    if not force and not should_check_updates(config):
        return
    
    # Perform update check
    try:
        registry = ReleaseRegistry()
        current_version_getter = getattr(registry, "get_current_version", None)
        current_version = current_version_getter() if callable(current_version_getter) else _get_current_version()
        
        try:
            latest_release = registry.fetch_latest(channel="stable")
        except Exception as e:
            # GitHub API error, fail silently (don't block startup)
            print(f"Update check failed: {e}")
            set_last_check_time()  # Record attempt to avoid spam
            return
        
        # No releases found
        if latest_release is None:
            set_last_check_time()
            return
        
        # Check compatibility (if manifest provided)
        if manifest_path:
            checker = CompatibilityChecker()
            import yaml
            with open(manifest_path, "r") as f:
                manifest = yaml.safe_load(f)
            
            result = checker.check(
                current_version=current_version,
                target_version=latest_release.version,
                manifest=manifest,
            )
            
            if not result.compatible:
                # Incompatible version, don't notify
                set_last_check_time()
                return
        
        # Check if update available
        if latest_release.version == current_version:
            # Already on latest version
            set_last_check_time()
            return
        
        # Build notification
        breaking_changes = _extract_breaking_changes(latest_release)
        notification = UpdateNotification(
            title=f"Vitruvyan Core Update Available: v{latest_release.version}",
            message=f"New version v{latest_release.version} is available (current: v{current_version})",
            current_version=current_version,
            available_version=latest_release.version,
            breaking_changes=breaking_changes,
            urgency="critical" if breaking_changes else "normal",
            changelog_url=registry.get_release_url(latest_release.version),
        )
        
        # Send notifications
        _send_notifications(notification, config)
        
        # Record last check time
        set_last_check_time()
    
    except Exception as e:
        # Don't let notification errors block system startup
        print(f"Startup update check failed: {e}")
        import traceback
        traceback.print_exc()


def _send_notifications(notification: UpdateNotification, config: NotificationConfig) -> None:
    """
    Send notifications to configured channels.
    
    Args:
        notification: Update notification data
        config: Notification configuration
    """
    for channel in config.channels:
        try:
            if channel == NotificationChannel.DESKTOP:
                notifier = DesktopNotifier(urgency=config.desktop_urgency)
                if notifier.is_available():
                    notifier.send(notification)
            
            elif channel == NotificationChannel.LOG:
                notifier = LogNotifier()
                notifier.send(notification)
            
            elif channel == NotificationChannel.WEBHOOK:
                if config.webhook_url:
                    notifier = WebhookNotifier(
                        webhook_url=config.webhook_url,
                        format=config.webhook_format,
                    )
                    if notifier.is_available():
                        notifier.send(notification)
            
            # EMAIL notifier placeholder (Phase 4 optional)
            # elif channel == NotificationChannel.EMAIL:
            #     if config.email_to:
            #         notifier = EmailNotifier(config)
            #         notifier.send(notification)
        
        except Exception as e:
            print(f"Failed to send notification via {channel.value}: {e}")
