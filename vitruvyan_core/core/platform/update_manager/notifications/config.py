"""
Notification configuration for Update Manager.

Reads configuration from:
1. Environment variables (override)
2. Vertical manifest (notification section)
3. Defaults (fallback)
"""

import os
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import yaml


def _state_dir() -> Path:
    """Resolve writable state dir under repo root when possible."""
    env_dir = os.getenv("VIT_STATE_DIR")
    if env_dir:
        return Path(env_dir)

    home_dir = Path.home() / ".vitruvyan"
    try:
        home_dir.mkdir(parents=True, exist_ok=True)
        return home_dir
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return Path(result.stdout.strip()) / ".vitruvyan"
    except Exception:
        return Path(".vitruvyan")


class NotificationChannel(Enum):
    """Available notification channels."""

    DESKTOP = "desktop"  # Desktop notifications (notify-send, osascript)
    LOG = "log"  # Log file (INFO level)
    WEBHOOK = "webhook"  # HTTP webhook (Slack, generic)
    EMAIL = "email"  # Email (SMTP)


@dataclass
class NotificationConfig:
    """Notification system configuration."""

    enabled: bool = True
    channels: List[NotificationChannel] = None
    check_interval_hours: int = 24  # How often to check for updates
    check_on_startup: bool = True  # Check on system startup
    only_notify_critical: bool = False  # Only notify for breaking changes
    
    # Webhook config
    webhook_url: Optional[str] = None
    webhook_format: str = "slack"  # "slack" | "generic"
    
    # Email config
    email_to: Optional[str] = None
    email_from: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Desktop config
    desktop_urgency: str = "normal"  # "low" | "normal" | "critical"

    def __post_init__(self):
        if self.channels is None:
            # Default: desktop + log
            self.channels = [NotificationChannel.DESKTOP, NotificationChannel.LOG]


def load_notification_config(manifest_path: Optional[str] = None) -> NotificationConfig:
    """
    Load notification configuration.

    Priority (highest to lowest):
    1. Environment variables (VIT_NOTIFY_*)
    2. Vertical manifest (notifications section)
    3. Defaults
    
    Args:
        manifest_path: Path to vertical_manifest.yaml (optional)
    
    Returns:
        NotificationConfig instance
    """
    config = NotificationConfig()
    
    # 1. Read from manifest (if provided)
    if manifest_path and Path(manifest_path).exists():
        with open(manifest_path, "r") as f:
            manifest = yaml.safe_load(f)
        
        notifications = manifest.get("notifications", {})
        if notifications:
            config.enabled = notifications.get("enabled", config.enabled)
            config.check_interval_hours = notifications.get(
                "check_interval_hours", config.check_interval_hours
            )
            config.check_on_startup = notifications.get(
                "check_on_startup", config.check_on_startup
            )
            config.only_notify_critical = notifications.get(
                "only_notify_critical", config.only_notify_critical
            )
            
            # Parse channels
            channels_str = notifications.get("channels", [])
            if channels_str:
                config.channels = [
                    NotificationChannel(ch) for ch in channels_str
                ]
            
            # Webhook config
            if "webhook_url" in notifications:
                config.webhook_url = notifications["webhook_url"]
            if "webhook_format" in notifications:
                config.webhook_format = notifications["webhook_format"]
            
            # Email config
            if "email_to" in notifications:
                config.email_to = notifications["email_to"]
            if "email_from" in notifications:
                config.email_from = notifications["email_from"]
            if "smtp_host" in notifications:
                config.smtp_host = notifications["smtp_host"]
            if "smtp_port" in notifications:
                config.smtp_port = notifications["smtp_port"]
            if "smtp_username" in notifications:
                config.smtp_username = notifications["smtp_username"]
            # Note: smtp_password read from env only (security)
    
    # 2. Override with environment variables
    if "VIT_NOTIFY_ENABLED" in os.environ:
        config.enabled = os.getenv("VIT_NOTIFY_ENABLED", "1") == "1"
    
    if "VIT_NOTIFY_INTERVAL" in os.environ:
        config.check_interval_hours = int(os.getenv("VIT_NOTIFY_INTERVAL", "24"))
    
    if "VIT_NOTIFY_ON_STARTUP" in os.environ:
        config.check_on_startup = os.getenv("VIT_NOTIFY_ON_STARTUP", "1") == "1"
    
    if "VIT_NOTIFY_CHANNELS" in os.environ:
        channels_env = os.getenv("VIT_NOTIFY_CHANNELS", "desktop,log")
        config.channels = [
            NotificationChannel(ch.strip()) for ch in channels_env.split(",")
        ]
    
    if "VIT_NOTIFY_WEBHOOK_URL" in os.environ:
        config.webhook_url = os.getenv("VIT_NOTIFY_WEBHOOK_URL")
    
    if "VIT_NOTIFY_EMAIL_TO" in os.environ:
        config.email_to = os.getenv("VIT_NOTIFY_EMAIL_TO")
    
    if "VIT_SMTP_PASSWORD" in os.environ:
        config.smtp_password = os.getenv("VIT_SMTP_PASSWORD")
    
    return config


def get_last_check_time() -> Optional[float]:
    """
    Get timestamp of last update check.
    
    Returns:
        Unix timestamp or None if never checked
    """
    state_file = _state_dir() / "last_update_check"
    try:
        if state_file.exists():
            return float(state_file.read_text().strip())
    except Exception:
        return None
    return None


def set_last_check_time(timestamp: Optional[float] = None) -> None:
    """
    Save timestamp of last update check.
    
    Args:
        timestamp: Unix timestamp (defaults to now)
    """
    import time
    
    timestamp = timestamp or time.time()
    state_file = _state_dir() / "last_update_check"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(str(timestamp))
