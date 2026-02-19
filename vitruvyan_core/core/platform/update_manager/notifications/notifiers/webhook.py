"""
Webhook notifier — Send notifications to HTTP webhooks (Slack, generic).
"""

import json
from typing import Optional

from .base import BaseNotifier, UpdateNotification


class WebhookNotifier(BaseNotifier):
    """Webhook notification sender (Slack, generic HTTP POST)."""

    def __init__(self, webhook_url: str, format: str = "slack"):
        """
        Initialize webhook notifier.
        
        Args:
            webhook_url: Webhook URL (Slack incoming webhook or generic HTTP endpoint)
            format: Webhook format ("slack" | "generic")
        """
        self.webhook_url = webhook_url
        self.format = format

    def send(self, notification: UpdateNotification) -> bool:
        """Send notification via webhook."""
        try:
            import httpx  # Optional dependency
            
            if self.format == "slack":
                payload = self._build_slack_payload(notification)
            else:
                payload = self._build_generic_payload(notification)
            
            response = httpx.post(
                self.webhook_url,
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()
            return True
        
        except ImportError:
            print("Webhook notification failed: httpx not installed")
            print("Install: pip install httpx")
            return False
        
        except Exception as e:
            print(f"Webhook notification failed: {e}")
            return False

    def is_available(self) -> bool:
        """Check if webhook notifier is available (httpx installed)."""
        try:
            import httpx  # noqa: F401
            return True
        except ImportError:
            return False

    def _build_slack_payload(self, notification: UpdateNotification) -> dict:
        """Build Slack-compatible webhook payload."""
        # Color based on urgency
        color_map = {
            "low": "#36a64f",  # green
            "normal": "#2196F3",  # blue
            "critical": "#ff0000",  # red
        }
        color = color_map.get(notification.urgency, "#2196F3")
        
        # Build fields
        fields = [
            {
                "title": "Current Version",
                "value": notification.current_version,
                "short": True,
            },
            {
                "title": "Available Version",
                "value": notification.available_version,
                "short": True,
            },
        ]
        
        if notification.breaking_changes:
            breaking_text = "\n".join(
                f"• {change}" for change in notification.breaking_changes[:5]
            )
            fields.append({
                "title": f"Breaking Changes ({len(notification.breaking_changes)})",
                "value": breaking_text,
                "short": False,
            })
        
        # Build attachment
        attachment = {
            "color": color,
            "title": notification.title,
            "text": notification.message,
            "fields": fields,
            "footer": "Vitruvyan Update Manager",
            "ts": int(__import__("time").time()),
        }
        
        if notification.changelog_url:
            attachment["title_link"] = notification.changelog_url
        
        return {"attachments": [attachment]}

    def _build_generic_payload(self, notification: UpdateNotification) -> dict:
        """Build generic JSON payload."""
        return {
            "title": notification.title,
            "message": notification.message,
            "current_version": notification.current_version,
            "available_version": notification.available_version,
            "breaking_changes": notification.breaking_changes,
            "urgency": notification.urgency,
            "changelog_url": notification.changelog_url,
            "timestamp": __import__("time").time(),
        }
