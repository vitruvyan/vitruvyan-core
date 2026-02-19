"""
Desktop notifier — Cross-platform desktop notifications.

Supports:
- Linux: notify-send (libnotify)
- macOS: osascript (AppleScript)
- Windows: win10toast (fallback: log)
"""

import platform
import subprocess
import sys

from .base import BaseNotifier, UpdateNotification


class DesktopNotifier(BaseNotifier):
    """Desktop notification sender (cross-platform)."""

    def __init__(self, urgency: str = "normal"):
        """
        Initialize desktop notifier.
        
        Args:
            urgency: Notification urgency ("low", "normal", "critical")
        """
        self.urgency = urgency
        self.platform = platform.system()

    def send(self, notification: UpdateNotification) -> bool:
        """Send desktop notification."""
        if self.platform == "Linux":
            return self._send_linux(notification)
        elif self.platform == "Darwin":  # macOS
            return self._send_macos(notification)
        elif self.platform == "Windows":
            return self._send_windows(notification)
        else:
            # Unknown platform, log only
            print(f"[Desktop Notification] {notification.title}: {notification.message}")
            return True

    def is_available(self) -> bool:
        """Check if desktop notifications are available."""
        if self.platform == "Linux":
            # Check for notify-send
            try:
                subprocess.run(
                    ["which", "notify-send"],
                    capture_output=True,
                    check=True,
                    timeout=2,
                )
                return True
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                return False
        
        elif self.platform == "Darwin":
            # macOS osascript always available
            return True
        
        elif self.platform == "Windows":
            # Check for win10toast (optional dependency)
            try:
                import win10toast  # noqa: F401
                return True
            except ImportError:
                return False
        
        return False

    def _send_linux(self, notification: UpdateNotification) -> bool:
        """Send notification via notify-send (Linux)."""
        try:
            urgency_map = {"low": "low", "normal": "normal", "critical": "critical"}
            urgency = urgency_map.get(notification.urgency, "normal")
            
            cmd = [
                "notify-send",
                "-u", urgency,
                "-a", "Vitruvyan Update Manager",
                notification.title,
                notification.message,
            ]
            
            subprocess.run(cmd, check=True, timeout=5)
            return True
        
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f"Desktop notification failed (Linux): {e}")
            return False

    def _send_macos(self, notification: UpdateNotification) -> bool:
        """Send notification via osascript (macOS)."""
        try:
            script = f'''
            display notification "{notification.message}" \
                with title "Vitruvyan Update Manager" \
                subtitle "{notification.title}"
            '''
            
            subprocess.run(
                ["osascript", "-e", script],
                check=True,
                timeout=5,
            )
            return True
        
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f"Desktop notification failed (macOS): {e}")
            return False

    def _send_windows(self, notification: UpdateNotification) -> bool:
        """Send notification via win10toast (Windows)."""
        try:
            from win10toast import ToastNotifier
            
            toaster = ToastNotifier()
            toaster.show_toast(
                title=notification.title,
                msg=notification.message,
                duration=10,  # seconds
                threaded=True,
            )
            return True
        
        except ImportError:
            print(f"Desktop notification failed (Windows): win10toast not installed")
            print(f"Install: pip install win10toast")
            return False
        
        except Exception as e:
            print(f"Desktop notification failed (Windows): {e}")
            return False
