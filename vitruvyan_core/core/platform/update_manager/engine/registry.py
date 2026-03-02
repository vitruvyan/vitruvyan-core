"""
Release Registry (GitHub Releases API Client)

Fetch strategy (two-pass, most resilient):
  Pass 1 — GitHub Releases API (/repos/{repo}/releases): for repos where
            formal Releases were created via GitHub UI or API. Assets are
            preferred source for releases.json.
  Pass 2 — GitHub Tags API (/repos/{repo}/tags): catches ALL pushed git
            tags, including those never converted to GitHub Releases.
            releases.json is fetched via Contents API at the tag ref.

This means a plain `git tag vX.Y.Z && git push --tags` is enough for the
release to be discovered by `vit upgrade` on any installation.

Environment Variables:
  GITHUB_TOKEN — Personal access token (required for private repos).
                  Read-only scope (`repo` for private, `public_repo` for
                  public repos) is sufficient.
  VITRUVYAN_REPO — Override repo (format: "owner/repo").
"""

import base64
import json
import logging
import os
import subprocess
from typing import List, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from ..engine.models import Release

logger = logging.getLogger(__name__)


class NetworkError(Exception):
    """GitHub API unreachable or rate-limited."""
    pass


class ReleaseRegistry:
    """
    Fetch Core releases from GitHub.
    
    Methods:
    - fetch_latest(channel="stable") → Release
    - fetch_all(channel=None) → List[Release]
    - verify_checksum(release) → bool
    
    Environment Variables:
    - GITHUB_TOKEN: Personal access token for private repositories (optional)
    """
    
    GITHUB_API_BASE = "https://api.github.com"
    TIMEOUT_SECONDS = 10
    
    def __init__(self, repo: Optional[str] = None):
        """
        Initialize registry client.
        
        Args:
            repo: GitHub repository (format: "owner/repo").
                  If None, autodetermines from git remote or VITRUVYAN_REPO env var.
        """
        if repo is None:
            repo = self._autodetermine_repo()
        
        self.repo = repo
        self.api_url = f"{self.GITHUB_API_BASE}/repos/{repo}/releases"
        self.github_token = os.getenv("GITHUB_TOKEN") or self._autodetermine_token()
    
    def _autodetermine_repo(self) -> str:
        """
        Autodetermine repository from git remote or environment variable.
        
        Returns:
            Repository name (format: "owner/repo")
        """
        # 1. Environment variable (highest priority)
        repo = os.getenv("VITRUVYAN_REPO")
        if repo:
            logger.debug(f"Using repository from VITRUVYAN_REPO: {repo}")
            return repo

        # 2. vertical_manifest.yaml — upstream.repo (downstream vertical config)
        try:
            import yaml
            current = os.getcwd()
            while current != "/":
                manifest_path = os.path.join(current, "vertical_manifest.yaml")
                if os.path.exists(manifest_path):
                    with open(manifest_path, "r") as f:
                        manifest = yaml.safe_load(f) or {}
                    upstream_repo = manifest.get("upstream", {}).get("repo")
                    if upstream_repo:
                        logger.debug(f"Using repository from vertical_manifest.yaml upstream.repo: {upstream_repo}")
                        return upstream_repo
                    break
                if os.path.exists(os.path.join(current, ".git")):
                    break
                parent = os.path.dirname(current)
                if parent == current:
                    break
                current = parent
        except Exception as e:
            logger.debug(f"Could not read vertical manifest for upstream repo: {e}")

        # 3. git remote origin — supports github.com HTTPS and SSH
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            remote_url = result.stdout.strip()
            
            # Parse GitHub URL (supports both HTTPS and SSH)
            # https://github.com/owner/repo.git
            # git@github.com:owner/repo.git
            if "github.com" in remote_url:
                parts = remote_url.replace(".git", "").split("/")
                if len(parts) >= 2:
                    owner = parts[-2].split(":")[-1]  # Handle git@github.com:owner
                    # git@github-alias:owner/repo.git  (SSH alias — strip host, parse owner/repo)
                    repo = parts[-1]
                    detected_repo = f"{owner}/{repo}"
                    logger.debug(f"Autodetermined repository from git remote: {detected_repo}")
                    return detected_repo
        
        except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
            pass

        # 4. Fallback to default
        default_repo = "vitruvyan/vitruvyan-core"
        logger.debug(f"Using default repository: {default_repo}")
        return default_repo

    def _autodetermine_token(self) -> Optional[str]:
        """
        Autodetermine GitHub token from gh CLI if GITHUB_TOKEN env var is not set.

        Uses `gh auth token` to retrieve the token from the GitHub CLI.
        Returns None if gh CLI is not installed or not authenticated.
        """
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                token = result.stdout.strip()
                logger.debug("Autodetermined GitHub token from gh CLI")
                return token
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        return None
    
    def _create_request(self, url: str, accept_header: str = "application/vnd.github.v3+json") -> Request:
        """
        Create HTTP request with authentication if token is available.
        
        Args:
            url: Request URL
            accept_header: Accept header value
        
        Returns:
            Request object with headers
        """
        headers = {"Accept": accept_header}
        
        # Add authentication if token is available
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
            logger.debug("Using GitHub token for authentication")
        
        return Request(url, headers=headers)
    
    def fetch_latest(self, channel="stable") -> Optional[Release]:
        """
        Fetch latest release for channel.

        Args:
            channel: "stable" or "beta"

        Returns:
            Release object (highest SemVer for channel), or None.

        Raises:
            NetworkError: GitHub API unreachable.
        """
        all_releases = self.fetch_all(channel=channel)
        if not all_releases:
            logger.warning(f"No {channel} releases found in {self.repo}")
            return None

        sorted_releases = sorted(
            all_releases,
            key=lambda r: self._parse_semver(r.version),
            reverse=True,
        )
        return sorted_releases[0]

    def fetch_all(self, channel: Optional[str] = None) -> List[Release]:
        """
        Fetch all releases (optionally filtered by channel).

        Two-pass strategy:
          Pass 1 — GitHub Releases API: formal releases with release assets.
          Pass 2 — GitHub Tags API: plain git tags (git push --tags).
                   releases.json is fetched via Contents API at the tag ref.

        Args:
            channel: "stable", "beta", or None (all channels).

        Returns:
            List of Release objects (sorted by version descending).

        Raises:
            NetworkError: GitHub API unreachable.
        """
        releases: List[Release] = []
        seen_versions: set = set()

        # ── Pass 1: GitHub Releases API ───────────────────────────────────
        try:
            request = self._create_request(
                f"{self.api_url}?per_page=100",
                accept_header="application/vnd.github.v3+json",
            )
            with urlopen(request, timeout=self.TIMEOUT_SECONDS) as response:
                releases_data = json.loads(response.read().decode())

            if not isinstance(releases_data, list):
                logger.warning(
                    "GitHub Releases API returned unexpected type: %s — "
                    "token may be missing or repo not found",
                    type(releases_data).__name__,
                )
                releases_data = []
            else:
                logger.info(
                    "Pass 1: fetched %d GitHub Releases from %s",
                    len(releases_data), self.repo,
                )

            for gh_release in releases_data:
                tag_name = gh_release.get("tag_name", "")
                if not tag_name:
                    continue

                metadata = self._metadata_from_release_asset(gh_release)
                if not metadata:
                    # No asset — will be retried in Pass 2 via Contents API
                    continue

                release = self._parse_release(metadata, tag_name, channel)
                if release and release.version not in seen_versions:
                    releases.append(release)
                    seen_versions.add(release.version)

        except (URLError, HTTPError) as e:
            # Pass 1 failure is non-fatal — Pass 2 may succeed alone.
            logger.warning("Pass 1 (Releases API) failed: %s — falling back to Tags API", e)
        except json.JSONDecodeError as e:
            logger.warning("Pass 1: invalid JSON from Releases API: %s", e)

        # ── Pass 2: GitHub Tags API ────────────────────────────────────────
        try:
            tags_url = f"{self.GITHUB_API_BASE}/repos/{self.repo}/tags?per_page=100"
            request = self._create_request(tags_url)
            with urlopen(request, timeout=self.TIMEOUT_SECONDS) as response:
                tags_data = json.loads(response.read().decode())

            if not isinstance(tags_data, list):
                raise NetworkError(
                    f"GitHub Tags API returned unexpected response "
                    f"(repo={self.repo!r}, type={type(tags_data).__name__}). "
                    "Check that GITHUB_TOKEN is set and has repo read access."
                )

            logger.info(
                "Pass 2: fetched %d tags from %s", len(tags_data), self.repo
            )

            for tag in tags_data:
                tag_name = tag.get("name", "")
                if not tag_name:
                    continue

                # Extract clean version (strip leading "v")
                version = tag_name.lstrip("v")
                if version in seen_versions:
                    # Already covered by Pass 1
                    continue

                # Fetch releases.json from repo contents at this tag ref
                metadata = self._metadata_from_contents_api(tag_name)
                if not metadata:
                    logger.debug(
                        "Skipping tag %s: no releases.json found at ref", tag_name
                    )
                    continue

                release = self._parse_release(metadata, tag_name, channel)
                if release and release.version not in seen_versions:
                    releases.append(release)
                    seen_versions.add(release.version)

        except NetworkError:
            raise
        except (URLError, HTTPError) as e:
            raise NetworkError(f"GitHub Tags API error: {e}") from e
        except json.JSONDecodeError as e:
            raise NetworkError(f"Invalid JSON from Tags API: {e}") from e

        # Sort by SemVer descending
        releases.sort(key=lambda r: self._parse_semver(r.version), reverse=True)
        logger.info(
            "fetch_all: %d releases found (channel=%s)", len(releases), channel or "all"
        )
        return releases

    # ── Metadata sources ──────────────────────────────────────────────────

    def _metadata_from_release_asset(self, gh_release: dict) -> Optional[dict]:
        """
        Download releases.json from a GitHub Release *asset*.

        Args:
            gh_release: GitHub Release API response dict.

        Returns:
            Parsed releases.json dict, or None if no asset found.
        """
        assets = gh_release.get("assets", [])
        metadata_asset = next(
            (a for a in assets if a.get("name") == "releases.json"), None
        )
        if not metadata_asset:
            return None

        asset_url = metadata_asset.get("url")  # API URL (not browser_download_url)
        if not asset_url:
            return None

        try:
            request = self._create_request(
                asset_url, accept_header="application/octet-stream"
            )
            with urlopen(request, timeout=self.TIMEOUT_SECONDS) as response:
                return json.loads(response.read().decode())
        except (URLError, HTTPError, json.JSONDecodeError) as e:
            logger.warning(
                "Failed to download releases.json asset from release %s: %s",
                gh_release.get("tag_name", "?"), e,
            )
            return None

    def _metadata_from_contents_api(self, tag_ref: str) -> Optional[dict]:
        """
        Fetch releases.json directly from repo file tree at *tag_ref*.

        Uses GitHub Contents API:
          GET /repos/{owner}/{repo}/contents/releases.json?ref={tag_ref}

        This works for any pushed git tag — no GitHub Release required.

        Args:
            tag_ref: Git tag name (e.g., "v1.8.0").

        Returns:
            Parsed releases.json dict, or None if not found / parse error.
        """
        url = (
            f"{self.GITHUB_API_BASE}/repos/{self.repo}"
            f"/contents/releases.json?ref={tag_ref}"
        )
        try:
            request = self._create_request(url)
            with urlopen(request, timeout=self.TIMEOUT_SECONDS) as response:
                content_meta = json.loads(response.read().decode())

            # GitHub Contents API returns file content base64-encoded
            encoding = content_meta.get("encoding", "")
            raw_content = content_meta.get("content", "")

            if encoding == "base64":
                decoded = base64.b64decode(raw_content).decode("utf-8")
            else:
                # Fallback: download_url
                download_url = content_meta.get("download_url")
                if not download_url:
                    logger.warning(
                        "Contents API: unexpected encoding %r for tag %s",
                        encoding, tag_ref,
                    )
                    return None
                req2 = self._create_request(download_url)
                with urlopen(req2, timeout=self.TIMEOUT_SECONDS) as r2:
                    decoded = r2.read().decode("utf-8")

            return json.loads(decoded)

        except HTTPError as e:
            if e.code == 404:
                # releases.json not present in this tag — silent skip
                return None
            logger.warning(
                "Contents API HTTP %d for tag %s: %s", e.code, tag_ref, e
            )
            return None
        except (URLError, json.JSONDecodeError, KeyError) as e:
            logger.warning(
                "Contents API error for tag %s: %s", tag_ref, e
            )
            return None

    # ── Internal helpers ──────────────────────────────────────────────────

    def _parse_release(
        self,
        metadata: dict,
        tag_name: str,
        channel_filter: Optional[str],
    ) -> Optional[Release]:
        """
        Build a Release object from releases.json metadata.

        Args:
            metadata:       Parsed releases.json dict.
            tag_name:       Source git tag name (for logging).
            channel_filter: If set, skip releases that don't match.

        Returns:
            Release object, or None if filtered out / invalid.
        """
        release_channel = metadata.get("channel", "stable")
        if channel_filter and release_channel != channel_filter:
            logger.debug("Skipping %s (channel=%s)", tag_name, release_channel)
            return None

        try:
            return Release(
                version=metadata["version"],
                release_date=metadata["release_date"],
                channel=release_channel,
                contracts_version=metadata.get("contracts_version", ""),
                changes=metadata.get("changes", {}),
                migration_guide_url=metadata.get("migration_guide_url"),
                minimum_vertical_version=metadata.get("minimum_vertical_version", {}),
                checksum=metadata.get("checksum", {}),
            )
        except KeyError as e:
            logger.warning(
                "Invalid releases.json for tag %s: missing field %s", tag_name, e
            )
            return None

    def _download_release_metadata(self, gh_release: dict) -> Optional[dict]:
        """
        Backward-compatible alias for _metadata_from_release_asset().

        Kept for any external callers that used the old method name.
        """
        return self._metadata_from_release_asset(gh_release)

    
    def verify_checksum(self, release: Release) -> bool:
        """
        Verify release artifact checksum (Git commit SHA).
        
        Args:
            release: Release object with checksum metadata
        
        Returns:
            True if checksum matches, False otherwise
        
        Raises:
            ValueError: Unsupported checksum type
        """
        checksum_type = release.checksum.get("type")
        expected_sha = release.checksum.get("value")
        
        if not expected_sha:
            logger.warning(f"Release {release.version} has no checksum")
            return False
        
        if checksum_type != "git_commit_sha":
            raise ValueError(f"Unsupported checksum type: {checksum_type}")
        
        # Verify Git commit SHA
        tag = f"v{release.version}"
        try:
            result = subprocess.run(
                ["git", "rev-parse", tag],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            actual_sha = result.stdout.strip()
            
            if actual_sha != expected_sha:
                logger.error(
                    f"Checksum mismatch for {release.version}: "
                    f"expected={expected_sha}, actual={actual_sha}"
                )
                return False
            
            logger.info(f"Checksum verified for {release.version}: {actual_sha}")
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr}")
            return False
        
        except FileNotFoundError:
            logger.error("git command not found (install Git)")
            return False
    
    def _parse_semver(self, version: str) -> tuple:
        """
        Parse SemVer string into comparable tuple.
        
        Args:
            version: SemVer string (e.g., "1.2.3" or "1.2.3-beta.1")
        
        Returns:
            Tuple: (major, minor, patch, prerelease_tuple)
            Example: "1.2.3-beta.1" → (1, 2, 3, ('beta', 1))
                     "1.2.3" → (1, 2, 3, ())
        """
        # Strip 'v' prefix if present
        version = version.lstrip("v")
        
        # Split version and prerelease
        if "-" in version:
            base_version, prerelease = version.split("-", 1)
        else:
            base_version, prerelease = version, ""
        
        # Parse base version (major.minor.patch)
        parts = base_version.split(".")
        try:
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
        except ValueError:
            logger.warning(f"Invalid SemVer: {version}")
            return (0, 0, 0, ())
        
        # Parse prerelease (beta.1, alpha.2, etc.)
        prerelease_tuple = ()
        if prerelease:
            prerelease_parts = prerelease.split(".")
            # Convert numeric parts to int for proper sorting
            prerelease_tuple = tuple(
                int(p) if p.isdigit() else p
                for p in prerelease_parts
            )
        
        # Return comparable tuple
        # Note: versions with prerelease sort LOWER than stable versions
        # (1, 2, 3, ()) > (1, 2, 3, ('beta', 1))
        return (major, minor, patch, prerelease_tuple)
