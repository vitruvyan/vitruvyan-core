"""
Log notifier — Write update notifications to log file.
"""

import logging
from pathlib import Path

from .base import BaseNotifier, UpdateNotification


class LogNotifier(BaseNotifier):
    """Log-based notification sender."""

    def __init__(self, log_file: str = None):
        """
        Initialize log notifier.
        
        Args:
            log_file: Path to log file (defaults to ~/.vitruvyan/update_notifications.log)
        """
        if log_file is None:
            log_file = Path.home() / ".vitruvyan" / "update_notifications.log"
        
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger("vitruvyan.update_manager.notifications")
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file)
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def send(self, notification: UpdateNotification) -> bool:
        """Write notification to log file."""
        try:
            log_message = (
                f"{notification.title}\n"
                f"  Message: {notification.message}\n"
                f"  Current: {notification.current_version}\n"
                f"  Available: {notification.available_version}\n"
            )
            
            if notification.breaking_changes:
                log_message += f"  Breaking changes: {len(notification.breaking_changes)}\n"
                for change in notification.breaking_changes[:3]:  # Show first 3
                    log_message += f"    - {change}\n"
            
            if notification.changelog_url:
                log_message += f"  Changelog: {notification.changelog_url}\n"
            
            # Log level based on urgency
            if notification.urgency == "critical":
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)
            
            return True
        
        except Exception as e:
            print(f"Log notification failed: {e}")
            return False

    def is_available(self) -> bool:
        """Log notifier is always available."""
        return True
