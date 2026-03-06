"""
vit release command - Validate and preview local release metadata.

This lightweight command intentionally avoids network side effects.
"""

import argparse
import json
from pathlib import Path


def _load_release_metadata() -> tuple[dict | None, Path | None]:
    """
    Load local release metadata from supported filenames.

    Supported order:
    1. release_metadata.json (contract name)
    2. releases.json (legacy name)
    """
    candidates = [Path("release_metadata.json"), Path("releases.json")]
    for path in candidates:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f), path
            except Exception:
                return None, path
    return None, None


def cmd_release(args: argparse.Namespace) -> int:
    """
    Execute 'vit release' command.

    Current scope:
    - Validate local metadata readability.
    - Show version/channel summary.
    - --dry-run keeps behavior explicit and side-effect free.
    """
    metadata, path = _load_release_metadata()

    if path is None:
        print("❌ No release metadata found (expected release_metadata.json or releases.json)")
        return 1

    if metadata is None:
        print(f"❌ Invalid JSON in {path}")
        return 1

    version = metadata.get("version", "unknown")
    channel = metadata.get("channel", "stable")
    release_date = metadata.get("release_date", "unknown")

    print("📦 Release metadata loaded")
    print(f"   File: {path}")
    print(f"   Version: {version}")
    print(f"   Channel: {channel}")
    print(f"   Release date: {release_date}")

    if args.dry_run:
        print("\n✅ Dry-run complete (no API calls executed)")
        return 0

    print(
        "\n⚠️  Publish action not implemented in this build.\n"
        "   Use --dry-run to validate payload, then publish via CI workflow."
    )
    return 0


def register_release_command(subparsers):
    """Register 'vit release' subcommand."""
    parser = subparsers.add_parser(
        "release",
        help="Validate local release metadata (dry-run friendly)",
        description="Validate release metadata payload before CI/GitHub publication",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate metadata locally without network actions",
    )
    parser.set_defaults(func=cmd_release)
