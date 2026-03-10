"""
Tests for notification system (Phase 4).

Tests:
- NotificationConfig loading (manifest, env vars, defaults)
- Desktop notifier (mocked subprocess)
- Log notifier (file writes)
- Webhook notifier (mocked httpx)
- startup_check logic (last check time, interval)
- PeriodicPoller (mocked time.sleep)
"""

import json
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from core.platform.update_manager.notifications.config import (
    NotificationChannel,
    NotificationConfig,
    get_last_check_time,
    load_notification_config,
    set_last_check_time,
)
from core.platform.update_manager.notifications.notifiers import (
    DesktopNotifier,
    LogNotifier,
    UpdateNotification,
    WebhookNotifier,
)
from core.platform.update_manager.notifications.startup_check import (
    should_check_updates,
    startup_check,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_manifest(tmp_path):
    """Create sample vertical_manifest.yaml with notifications section."""
    manifest_path = tmp_path / "vertical_manifest.yaml"
    manifest_data = {
        "domain_name": "test",
        "compatibility": {"min_core_version": "1.0.0", "max_core_version": "1.x.x"},
        "notifications": {
            "enabled": True,
            "channels": ["desktop", "log"],
            "check_interval_hours": 12,
            "desktop_urgency": "normal",
        },
    }
    manifest_path.write_text(yaml.dump(manifest_data))
    return str(manifest_path)


@pytest.fixture
def sample_notification():
    """Create sample UpdateNotification."""
    return UpdateNotification(
        title="Update Available: v1.2.0",
        message="New version v1.2.0 is available (current: v1.0.0)",
        current_version="1.0.0",
        available_version="1.2.0",
        breaking_changes=False,
        urgency="normal",
        changelog_url="https://github.com/dbaldoni/vitruvyan-core/releases/tag/v1.2.0",
    )


# ============================================================================
# CONFIG TESTS
# ============================================================================


def test_load_config_defaults(tmp_path, monkeypatch):
    """Test loading config with all defaults."""
    # Clear env vars
    monkeypatch.delenv("VIT_NOTIFY_ENABLED", raising=False)
    
    config = load_notification_config(None)
    
    assert config.enabled is True
    assert NotificationChannel.DESKTOP in config.channels
    assert NotificationChannel.LOG in config.channels
    assert config.check_interval_hours == 24
    assert config.desktop_urgency == "normal"


def test_load_config_from_manifest(sample_manifest):
    """Test loading config from manifest."""
    config = load_notification_config(sample_manifest)
    
    assert config.enabled is True
    assert NotificationChannel.DESKTOP in config.channels
    assert NotificationChannel.LOG in config.channels
    assert config.check_interval_hours == 12  # From manifest (not default 24)


def test_load_config_env_override(sample_manifest, monkeypatch):
    """Test environment variables override manifest."""
    monkeypatch.setenv("VIT_NOTIFY_ENABLED", "0")
    monkeypatch.setenv("VIT_NOTIFY_CHANNELS", "webhook")
    monkeypatch.setenv("VIT_NOTIFY_WEBHOOK_URL", "https://hooks.slack.com/test")
    
    config = load_notification_config(sample_manifest)
    
    assert config.enabled is False  # Env var overrode manifest
    assert config.channels == [NotificationChannel.WEBHOOK]
    assert config.webhook_url == "https://hooks.slack.com/test"


def test_last_check_time(tmp_path, monkeypatch):
    """Test get/set_last_check_time."""
    # Override home directory
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    
    # First check: no timestamp
    assert get_last_check_time() is None
    
    # Set timestamp
    set_last_check_time()
    
    # Second check: timestamp exists
    timestamp = get_last_check_time()
    assert timestamp is not None
    assert isinstance(timestamp, float)
    assert timestamp <= time.time()


# ============================================================================
# NOTIFIER TESTS
# ============================================================================


@patch("subprocess.run")
def test_desktop_notifier_linux(mock_subprocess, sample_notification):
    """Test DesktopNotifier on Linux (notify-send)."""
    mock_subprocess.return_value = MagicMock(returncode=0)
    
    with patch("platform.system", return_value="Linux"):
        notifier = DesktopNotifier()
        notifier.send(sample_notification)
    
    # Verify subprocess.run called with notify-send
    mock_subprocess.assert_called_once()
    args = mock_subprocess.call_args[0][0]
    assert args[0] == "notify-send"
    assert "Update Available: v1.2.0" in args


@patch("subprocess.run")
def test_desktop_notifier_macos(mock_subprocess, sample_notification):
    """Test DesktopNotifier on macOS (osascript)."""
    mock_subprocess.return_value = MagicMock(returncode=0)
    
    with patch("platform.system", return_value="Darwin"):
        notifier = DesktopNotifier()
        notifier.send(sample_notification)
    
    # Verify subprocess.run called with osascript
    mock_subprocess.assert_called_once()
    args = mock_subprocess.call_args[0][0]
    assert args[0] == "osascript"
    assert "-e" in args


def test_log_notifier(tmp_path, monkeypatch, sample_notification):
    """Test LogNotifier writes to log file."""
    # Override home directory
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    
    notifier = LogNotifier()
    notifier.send(sample_notification)
    
    # Verify log file created
    log_file = tmp_path / ".vitruvyan" / "update_notifications.log"
    assert log_file.exists()
    
    # Verify log contents
    log_content = log_file.read_text()
    assert "Update Available: v1.2.0" in log_content
    assert "Current: 1.0.0" in log_content
    assert "Available: 1.2.0" in log_content


@patch("httpx.post")
def test_webhook_notifier_slack(mock_httpx, sample_notification):
    """Test WebhookNotifier with Slack format."""
    mock_httpx.return_value = MagicMock(status_code=200)
    
    notifier = WebhookNotifier(
        webhook_url="https://hooks.slack.com/test",
        format="slack",
    )
    notifier.send(sample_notification)
    
    # Verify httpx.post called
    mock_httpx.assert_called_once()
    args, kwargs = mock_httpx.call_args
    
    assert args[0] == "https://hooks.slack.com/test"
    assert "json" in kwargs
    
    # Verify Slack payload structure
    payload = kwargs["json"]
    assert "attachments" in payload
    assert payload["attachments"][0]["title"] == "Update Available: v1.2.0"


@patch("httpx.post")
def test_webhook_notifier_generic(mock_httpx, sample_notification):
    """Test WebhookNotifier with generic format."""
    mock_httpx.return_value = MagicMock(status_code=200)
    
    notifier = WebhookNotifier(
        webhook_url="https://example.com/webhook",
        format="generic",
    )
    notifier.send(sample_notification)
    
    # Verify httpx.post called
    mock_httpx.assert_called_once()
    args, kwargs = mock_httpx.call_args
    
    # Verify generic payload structure
    payload = kwargs["json"]
    assert payload["title"] == "Update Available: v1.2.0"
    assert payload["current_version"] == "1.0.0"
    assert payload["available_version"] == "1.2.0"


# ============================================================================
# STARTUP CHECK TESTS
# ============================================================================


def test_should_check_updates_first_run(sample_manifest, tmp_path, monkeypatch):
    """Test should_check_updates returns True on first run."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    
    config = load_notification_config(sample_manifest)
    assert should_check_updates(config) is True


def test_should_check_updates_interval_not_elapsed(sample_manifest, tmp_path, monkeypatch):
    """Test should_check_updates returns False if interval not elapsed."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    
    # Set last check to 1 hour ago
    set_last_check_time()
    
    config = load_notification_config(sample_manifest)
    # Config has 12h interval, only 1h elapsed
    assert should_check_updates(config) is False


def test_should_check_updates_disabled(sample_manifest, tmp_path, monkeypatch):
    """Test should_check_updates returns False if disabled."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("VIT_NOTIFY_ENABLED", "0")
    
    config = load_notification_config(sample_manifest)
    assert should_check_updates(config) is False


@patch("core.platform.update_manager.notifications.startup_check.ReleaseRegistry")
@patch("core.platform.update_manager.notifications.startup_check._send_notifications")
def test_startup_check_update_available(mock_send, mock_registry, sample_manifest, tmp_path, monkeypatch):
    """Test startup_check sends notification when update available."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    
    # Mock registry to return update
    mock_registry_instance = MagicMock()
    mock_registry_instance.get_current_version.return_value = "1.0.0"
    mock_registry_instance.fetch_latest.return_value = MagicMock(
        version="1.2.0",
        breaking_changes=False,
    )
    mock_registry.return_value = mock_registry_instance
    
    # Run startup check
    startup_check(manifest_path=sample_manifest, force=True)
    
    # Verify notification sent
    assert mock_send.called
    notification, config = mock_send.call_args[0]
    assert notification.current_version == "1.0.0"
    assert notification.available_version == "1.2.0"


@patch("core.platform.update_manager.notifications.startup_check.ReleaseRegistry")
@patch("core.platform.update_manager.notifications.startup_check._send_notifications")
def test_startup_check_already_latest(mock_send, mock_registry, sample_manifest, tmp_path, monkeypatch):
    """Test startup_check does not notify if already on latest."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    
    # Mock registry to return no update
    mock_registry_instance = MagicMock()
    mock_registry_instance.get_current_version.return_value = "1.2.0"
    mock_registry_instance.fetch_latest.return_value = MagicMock(
        version="1.2.0",
        breaking_changes=False,
    )
    mock_registry.return_value = mock_registry_instance
    
    # Run startup check
    startup_check(manifest_path=sample_manifest, force=True)
    
    # Verify notification NOT sent
    assert not mock_send.called


# ============================================================================
# PERIODIC POLLER TESTS
# ============================================================================


@patch("core.platform.update_manager.notifications.periodic_poller.startup_check")
@patch("time.sleep")
def test_periodic_poller_shutdown(mock_sleep, mock_startup_check, sample_manifest, tmp_path, monkeypatch):
    """Test PeriodicPoller handles graceful shutdown."""
    from core.platform.update_manager.notifications.periodic_poller import PeriodicPoller
    
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    
    # Create poller
    poller = PeriodicPoller(manifest_path=sample_manifest)
    
    # Mock sleep to trigger shutdown after first iteration
    def mock_sleep_shutdown(seconds):
        poller._shutdown_requested = True
    
    mock_sleep.side_effect = mock_sleep_shutdown
    
    # Start (should run once and exit)
    poller.start()
    
    # Verify startup_check called at least once
    assert mock_startup_check.called
