"""
Periodic poller — Background daemon for scheduled update checks.

Usage:
    # Run as background daemon
    python -m vitruvyan_core.core.platform.update_manager.notifications.periodic_poller
    
    # Or programmatically
    from core.platform.update_manager.notifications import PeriodicPoller
    
    poller = PeriodicPoller(manifest_path="vertical_manifest.yaml")
    poller.start()  # Blocking (runs until SIGINT/SIGTERM)
"""

import signal
import sys
import time
from pathlib import Path
from typing import Optional

from .config import load_notification_config
from .startup_check import startup_check


class PeriodicPoller:
    """
    Background daemon that periodically checks for Core updates.
    
    Features:
    - Runs in background (blocking loop, suitable for systemd/supervisord)
    - Respects check_interval_hours from config
    - Handles SIGINT/SIGTERM gracefully
    - Never blocks system startup (errors logged, not raised)
    """
    
    def __init__(self, manifest_path: Optional[str] = None):
        """
        Initialize periodic poller.
        
        Args:
            manifest_path: Path to vertical_manifest.yaml (optional)
        """
        self.manifest_path = manifest_path
        self._running = False
        self._shutdown_requested = False
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown on SIGINT/SIGTERM."""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self._shutdown_requested = True
    
    def start(self) -> None:
        """
        Start periodic update checks (blocking).
        
        Entry point for background daemon. Runs until SIGINT/SIGTERM received.
        """
        config = load_notification_config(self.manifest_path)
        
        if not config.enabled:
            print("Notifications disabled, periodic poller not starting")
            return
        
        print(f"Starting periodic update poller (interval: {config.check_interval_hours}h)")
        self._running = True
        
        # Run first check immediately
        self._check_updates()
        
        # Then run on schedule
        while self._running and not self._shutdown_requested:
            # Sleep in small increments to allow responsive shutdown
            interval_seconds = config.check_interval_hours * 3600
            sleep_increment = 60  # 1 minute
            
            elapsed = 0
            while elapsed < interval_seconds and not self._shutdown_requested:
                time.sleep(sleep_increment)
                elapsed += sleep_increment
            
            if not self._shutdown_requested:
                self._check_updates()
        
        print("Periodic poller shut down")
    
    def _check_updates(self) -> None:
        """Run update check (wraps startup_check with force=True)."""
        try:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking for updates...")
            startup_check(manifest_path=self.manifest_path, force=True)
        except Exception as e:
            print(f"Update check failed: {e}")
            import traceback
            traceback.print_exc()
    
    def stop(self) -> None:
        """Stop periodic poller."""
        self._running = False


def main():
    """
    CLI entry point for periodic poller.
    
    Usage:
        python -m vitruvyan_core.core.platform.update_manager.notifications.periodic_poller [manifest_path]
    """
    manifest_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    if manifest_path and not Path(manifest_path).exists():
        print(f"Error: Manifest file not found: {manifest_path}")
        sys.exit(1)
    
    poller = PeriodicPoller(manifest_path=manifest_path)
    poller.start()


def start_polling_daemon(manifest_path: Optional[str] = None) -> PeriodicPoller:
    """
    Helper function to start periodic poller programmatically.
    
    Usage:
        from core.platform.update_manager.notifications import start_polling_daemon
        
        poller = start_polling_daemon("vertical_manifest.yaml")
        # Poller runs in current thread (blocking)
    
    Args:
        manifest_path: Path to vertical_manifest.yaml (optional)
    
    Returns:
        PeriodicPoller instance (for testing/control)
    """
    poller = PeriodicPoller(manifest_path=manifest_path)
    poller.start()
    return poller


if __name__ == "__main__":
    main()
