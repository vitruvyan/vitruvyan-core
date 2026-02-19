"""
Output Formatters (Tables, Colors, JSON)

Phase 1 implementation.
"""

import json
from typing import Any


class OutputFormatter:
    """
    Format CLI output (human-readable + JSON).
    
    Methods:
    - table(data) → str (ASCII table)
    - color(text, color) → str (ANSI colored)
    - json_output(data) → str (JSON)
    """
    
    @staticmethod
    def table(data: list) -> str:
        """Render ASCII table."""
        raise NotImplementedError("Phase 1 implementation")
    
    @staticmethod
    def color(text: str, color: str) -> str:
        """
        Apply ANSI color.
        
        Colors: red, green, yellow, blue
        """
        colors = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "reset": "\033[0m"
        }
        return f"{colors.get(color, '')}{text}{colors['reset']}"
    
    @staticmethod
    def json_output(data: Any) -> str:
        """Format as JSON."""
        return json.dumps(data, indent=2)


def format_release_info(release) -> str:
    """
    Format Release object for display.
    
    Args:
        release: Release object
    
    Returns:
        Formatted string
    """
    lines = [
        f"Version: {release.version}",
        f"Channel: {release.channel}",
        f"Released: {release.release_date}",
        f"Contracts: {release.contracts_version}"
    ]
    
    if release.changes:
        changes = release.changes
        if changes.get("breaking"):
            lines.append(f"⚠️  Breaking changes: {len(changes['breaking'])}")
        if changes.get("features"):
            lines.append(f"✨ Features: {len(changes['features'])}")
        if changes.get("fixes"):
            lines.append(f"🐛 Fixes: {len(changes['fixes'])}")
    
    return "\n".join(lines)


def format_compatibility_result(result) -> str:
    """
    Format CompatibilityResult for display.
    
    Args:
        result: CompatibilityResult object
    
    Returns:
        Formatted string
    """
    if result.compatible:
        return f"✅ Compatible (target: {result.target_version})"
    else:
        return f"❌ Incompatible: {result.blocking_reason}"

