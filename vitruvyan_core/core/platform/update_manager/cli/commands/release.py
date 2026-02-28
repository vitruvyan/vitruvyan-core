"""
vit release — Create a GitHub Release from the current git tag.

Usage:
    vit release                      # auto-detect current tag
    vit release --tag v1.8.0         # explicit tag
    vit release --channel beta       # mark as beta channel
    vit release --dry-run            # print what would happen, no API calls

What this command does:
  1. Reads releases.json from the repo to locate the matching version entry.
  2. Creates a GitHub Release via the Releases API tagged at *tag*.
  3. Uploads releases.json as an asset on that Release so:
       - Installations with formal GitHub Releases get the fast (Pass 1) path.
       - All installations (including with only git tags) still work via the
         Tags API + Contents API fallback (Pass 2).

Prerequisites:
  - GITHUB_TOKEN env var must be set (needs repo write scope for private repos).
  - The tag must already be pushed: git push --tags

Environment Variables:
    GITHUB_TOKEN       GitHub personal access token (required).
    VITRUVYAN_REPO     Override repo slug (default: auto-detected from git remote).
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen, Request

from ...engine.registry import ReleaseRegistry, NetworkError

logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[9]  # vitruvyan-core/


def _find_repo_root() -> Path:
    """Walk up from this file until we find releases.json."""
    candidate = Path(__file__).resolve()
    for _ in range(15):
        candidate = candidate.parent
        if (candidate / "releases.json").exists():
            return candidate
    return Path.cwd()


def _git(*args, cwd: Optional[Path] = None) -> str:
    """Run a git command and return its stdout (stripped)."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
        cwd=str(cwd or _find_repo_root()),
    )
    return result.stdout.strip()


def _current_tag() -> Optional[str]:
    """Return the tag that points at HEAD, or None."""
    try:
        return _git("describe", "--tags", "--exact-match", "HEAD")
    except subprocess.CalledProcessError:
        return None


def _tag_pushed(tag: str) -> bool:
    """Return True if *tag* exists on origin."""
    try:
        _git("ls-remote", "--exit-code", "--tags", "origin", tag)
        return True
    except subprocess.CalledProcessError:
        return False


def _load_releases_json(repo_root: Path) -> dict:
    """Load releases.json from repo root."""
    path = repo_root / "releases.json"
    if not path.exists():
        raise FileNotFoundError(f"releases.json not found at {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


# ── GitHub API helpers ────────────────────────────────────────────────────────

def _make_request(
    url: str,
    method: str = "GET",
    body: Optional[bytes] = None,
    content_type: str = "application/json",
    token: Optional[str] = None,
    accept: str = "application/vnd.github.v3+json",
) -> Request:
    """Build an authenticated GitHub API request."""
    req = Request(url, data=body, method=method)
    req.add_header("Accept", accept)
    req.add_header("Content-Type", content_type)
    if token:
        req.add_header("Authorization", f"token {token}")
    return req


def _create_github_release(
    repo: str,
    tag: str,
    name: str,
    body: str,
    prerelease: bool,
    token: str,
    dry_run: bool = False,
) -> Optional[dict]:
    """
    Create a GitHub Release via the Releases API.

    Returns:
        API response dict (includes 'upload_url'), or None for dry-run.
    """
    url = f"https://api.github.com/repos/{repo}/releases"
    payload = json.dumps(
        {
            "tag_name": tag,
            "name": name,
            "body": body,
            "prerelease": prerelease,
            "draft": False,
        }
    ).encode("utf-8")

    if dry_run:
        print(f"[dry-run] POST {url}")
        print(f"[dry-run] payload: {json.loads(payload)}")
        return None

    req = _make_request(url, method="POST", body=payload, token=token)
    try:
        with urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        error_body = e.read().decode() if hasattr(e, "read") else ""
        raise NetworkError(
            f"GitHub API responded {e.code} when creating release {tag}: {error_body}"
        ) from e
    except URLError as e:
        raise NetworkError(f"Network error creating GitHub release: {e}") from e


def _upload_asset(
    upload_url_template: str,
    asset_name: str,
    content: bytes,
    token: str,
    dry_run: bool = False,
) -> None:
    """Upload a file as a GitHub Release asset."""
    # Strip the {?name,label} template suffix
    base_url = upload_url_template.split("{")[0]
    url = f"{base_url}?name={asset_name}&label={asset_name}"

    if dry_run:
        print(f"[dry-run] POST {url} ({len(content)} bytes)")
        return

    req = _make_request(
        url,
        method="POST",
        body=content,
        content_type="application/octet-stream",
        token=token,
    )
    try:
        with urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            logger.info("Uploaded asset: %s (%d bytes)", result.get("name"), result.get("size", 0))
    except HTTPError as e:
        error_body = e.read().decode() if hasattr(e, "read") else ""
        raise NetworkError(
            f"Failed to upload asset {asset_name}: HTTP {e.code} — {error_body}"
        ) from e
    except URLError as e:
        raise NetworkError(f"Network error uploading asset: {e}") from e


# ── Command ───────────────────────────────────────────────────────────────────

def cmd_release(args: argparse.Namespace) -> int:
    """
    Create a GitHub Release from the current (or specified) git tag.

    Returns:
        Exit code (0 = success, 1 = error).
    """
    repo_root = _find_repo_root()

    # ── Resolve tag ─────────────────────────────────────────────────────────
    tag = args.tag or _current_tag()
    if not tag:
        print(
            "❌  No tag found at HEAD. Tag your commit first:\n"
            "       git tag v1.8.0 && git push --tags",
            file=sys.stderr,
        )
        return 1

    if not tag.startswith("v"):
        tag = f"v{tag}"

    version = tag.lstrip("v")
    print(f"📦  Creating GitHub Release for tag: {tag}")

    # ── Verify tag is pushed ─────────────────────────────────────────────────
    if not args.dry_run and not _tag_pushed(tag):
        print(
            f"❌  Tag {tag} not found on origin. Push it first:\n"
            f"       git push --tags",
            file=sys.stderr,
        )
        return 1

    # ── Load releases.json ───────────────────────────────────────────────────
    try:
        metadata = _load_releases_json(repo_root)
    except FileNotFoundError as e:
        print(f"❌  {e}", file=sys.stderr)
        return 1

    # Find version entry in releases.json
    release_entry = None
    latest_version = metadata.get("version", "")
    if latest_version == version:
        release_entry = metadata
    else:
        # Check history / releases list if present
        for entry in metadata.get("releases", []):
            if entry.get("version") == version:
                release_entry = entry
                break

    if not release_entry:
        print(
            f"⚠️   Version {version} not found in releases.json (current: {latest_version}).\n"
            f"     Proceeding with top-level metadata.",
        )
        release_entry = metadata  # best effort

    # ── Build release body ───────────────────────────────────────────────────
    channel = args.channel or release_entry.get("channel", "stable")
    prerelease = channel != "stable"

    changes = release_entry.get("changes", {})
    body_lines = [f"## Vitruvyan Core v{version}\n", f"**Channel**: {channel}\n"]
    if changes:
        for section, items in changes.items():
            body_lines.append(f"\n### {section.title()}")
            if isinstance(items, list):
                for item in items:
                    body_lines.append(f"- {item}")
            else:
                body_lines.append(str(items))

    release_body = "\n".join(body_lines)

    # ── GitHub credentials ───────────────────────────────────────────────────
    token = os.getenv("GITHUB_TOKEN")
    if not token and not args.dry_run:
        print(
            "❌  GITHUB_TOKEN not set. Export it before running:\n"
            "       export GITHUB_TOKEN=<your-token>",
            file=sys.stderr,
        )
        return 1

    # ── Determine repo slug ──────────────────────────────────────────────────
    reg = ReleaseRegistry()
    repo_slug = reg.repo
    print(f"🔗  Repo: {repo_slug}")

    # ── Create Release ───────────────────────────────────────────────────────
    try:
        gh_release = _create_github_release(
            repo=repo_slug,
            tag=tag,
            name=f"v{version}",
            body=release_body,
            prerelease=prerelease,
            token=token or "",
            dry_run=args.dry_run,
        )
    except NetworkError as e:
        print(f"❌  {e}", file=sys.stderr)
        return 1

    if args.dry_run:
        print("✅  [dry-run] Release payload built successfully — no API calls made.")
        return 0

    release_url = gh_release.get("html_url", "?")
    upload_url = gh_release.get("upload_url", "")
    print(f"✅  GitHub Release created: {release_url}")

    # ── Upload releases.json asset ───────────────────────────────────────────
    if upload_url:
        try:
            releases_json_bytes = (repo_root / "releases.json").read_bytes()
            _upload_asset(
                upload_url_template=upload_url,
                asset_name="releases.json",
                content=releases_json_bytes,
                token=token or "",
            )
            print("📎  releases.json attached as release asset.")
        except NetworkError as e:
            print(f"⚠️   Asset upload failed (release still created): {e}", file=sys.stderr)

    print(f"\n🎉  Release v{version} ({channel}) published successfully.")
    print(f"     {release_url}")
    return 0


# ── Registration ──────────────────────────────────────────────────────────────

def register_release_command(subparsers: argparse._SubParsersAction) -> None:
    """Register `vit release` subcommand."""
    parser = subparsers.add_parser(
        "release",
        help="Create a GitHub Release from the current git tag",
        description=(
            "Publish the current (or specified) git tag as a GitHub Release "
            "and upload releases.json as an asset. "
            "Requires GITHUB_TOKEN env var."
        ),
    )
    parser.add_argument(
        "--tag",
        metavar="TAG",
        default=None,
        help="Git tag to release (default: tag at HEAD, e.g. v1.8.0)",
    )
    parser.add_argument(
        "--channel",
        choices=["stable", "beta"],
        default=None,
        help="Release channel (default: read from releases.json, fallback: stable)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without making any API calls",
    )
    parser.set_defaults(func=cmd_release)
