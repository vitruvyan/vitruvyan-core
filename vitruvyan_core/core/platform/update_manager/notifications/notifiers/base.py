"""
Base notifier interface for Update Manager notifications.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class UpdateNotification:
    """Update notification data."""

    title: str
    message: str
    current_version: str
    available_version: str
    breaking_changes: List[str]
    urgency: str = "normal"  # "low" | "normal" | "critical"
    changelog_url: Optional[str] = None


class BaseNotifier(ABC):
    """Abstract base class for notification senders."""

    @abstractmethod
    def send(self, notification: UpdateNotification) -> bool:
        """
        Send notification.
        
        Args:
            notification: Update notification data
        
        Returns:
            True if sent successfully, False otherwise
        """
        pass

    def is_available(self) -> bool:
        """
        Check if notifier is available (dependencies installed, config valid).
        
        Returns:
            True if notifier can be used
        """
        return True
