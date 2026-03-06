"""Persistent default channel helpers for vit CLI."""

import os
import subprocess
from pathlib import Path


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


def set_default_channel(channel: str) -> None:
    """Persist default channel."""
    state_dir = _state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "default_channel").write_text(channel, encoding="utf-8")


def get_default_channel() -> str:
    """
    Resolve channel with precedence:
    1. VIT_CHANNEL env var
    2. ~/.vitruvyan/default_channel
    3. stable
    """
    env_channel = os.getenv("VIT_CHANNEL")
    if env_channel in {"stable", "beta"}:
        return env_channel

    state_file = _state_dir() / "default_channel"
    if state_file.exists():
        value = state_file.read_text(encoding="utf-8").strip()
        if value in {"stable", "beta"}:
            return value

    return "stable"
