"""
Notification system for Update Manager.

Provides automatic update visibility through multiple channels:
- Startup check (on system boot)
- Periodic polling (background daemon)
- Desktop notifications (Linux, macOS, Windows)
- Webhook notifications (Slack, generic HTTP)
- Email notifications (SMTP)
- Log-based notifications

Usage:
    from vitruvyan_core.core.platform.update_manager.notifications import startup_check
    
    # Check for updates on startup
startup_check()
"""

from .startup_check import startup_check, should_check_updates
from .periodic_poller import PeriodicPoller, start_polling_daemon
from .config import NotificationConfig, NotificationChannel, load_notification_config

__all__ = [
    "startup_check",
    "should_check_updates",
    "PeriodicPoller",
    "start_polling_daemon",
    "NotificationConfig",
    "NotificationChannel",
    "load_notification_config",
]
