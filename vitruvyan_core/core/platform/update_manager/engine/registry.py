"""
Release Registry (GitHub Releases API Client)

Phase 1 implementation.
"""

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
        self.github_token = os.getenv("GITHUB_TOKEN")
    
    def _autodetermine_repo(self) -> str:
        """
        Autodetermine repository from git remote or environment variable.
        
        Returns:
            Repository name (format: "owner/repo")
        """
        # Try environment variable first
        repo = os.getenv("VITRUVYAN_REPO")
        if repo:
            logger.debug(f"Using repository from VITRUVYAN_REPO: {repo}")
            return repo
        
        # Try git remote
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
                    repo = parts[-1]
                    detected_repo = f"{owner}/{repo}"
                    logger.debug(f"Autodetermined repository from git remote: {detected_repo}")
                    return detected_repo
        
        except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
            pass
        
        # Fallback to default
        default_repo = "vitruvyan/vitruvyan-core"
        logger.debug(f"Using default repository: {default_repo}")
        return default_repo
    
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
            Release object (highest SemVer for channel)
        
        Raises:
            NetworkError: GitHub API unreachable
        """
        all_releases = self.fetch_all(channel=channel)
        if not all_releases:
            logger.warning(f"No {channel} releases found in {self.repo}")
            return None
        
        # Sort by SemVer (descending) and return first
        sorted_releases = sorted(
            all_releases,
            key=lambda r: self._parse_semver(r.version),
            reverse=True
        )
        return sorted_releases[0]
    
    def fetch_all(self, channel: Optional[str] = None) -> List[Release]:
        """
        Fetch all releases (optionally filtered by channel).
        
        Args:
            channel: "stable", "beta", or None (all channels)
        
        Returns:
            List of Release objects (sorted by version descending)
        
        Raises:
            NetworkError: GitHub API unreachable
        """
        try:
            # Fetch GitHub Releases (paginated, max 100)
            request = self._create_request(
                f"{self.api_url}?per_page=100",
                accept_header="application/vnd.github.v3+json"
            )
            
            with urlopen(request, timeout=self.TIMEOUT_SECONDS) as response:
                releases_data = json.loads(response.read().decode())
            
            logger.info(f"Fetched {len(releases_data)} releases from {self.repo}")
            
        except (URLError, HTTPError) as e:
            raise NetworkError(f"GitHub API error: {e}")
        except json.JSONDecodeError as e:
            raise NetworkError(f"Invalid JSON response: {e}")
        
        # Parse each release (download releases.json asset)
        releases = []
        for gh_release in releases_data:
            tag_name = gh_release.get("tag_name")
            if not tag_name:
                continue
            
            # Download releases.json asset
            metadata = self._download_release_metadata(gh_release)
            if not metadata:
                logger.debug(f"Skipping {tag_name} (no releases.json asset)")
                continue
            
            # Filter by channel
            release_channel = metadata.get("channel", "stable")
            if channel and release_channel != channel:
                logger.debug(f"Skipping {tag_name} (channel={release_channel})")
                continue
            
            # Parse Release object
            try:
                release = Release(
                    version=metadata["version"],
                    release_date=metadata["release_date"],
                    channel=release_channel,
                    contracts_version=metadata["contracts_version"],
                    changes=metadata.get("changes", {}),
                    migration_guide_url=metadata.get("migration_guide_url"),
                    minimum_vertical_version=metadata.get("minimum_vertical_version", {}),
                    checksum=metadata.get("checksum", {})
                )
                releases.append(release)
                logger.debug(f"Parsed release: {release.version} ({release.channel})")
            
            except KeyError as e:
                logger.warning(f"Invalid release metadata for {tag_name}: missing {e}")
                continue
        
        # Sort by SemVer (descending)
        releases.sort(key=lambda r: self._parse_semver(r.version), reverse=True)
        
        return releases
    
    def _download_release_metadata(self, gh_release: dict) -> Optional[dict]:
        """
        Download releases.json asset from GitHub Release.
        
        Args:
            gh_release: GitHub Release API response (dict)
        
        Returns:
            Parsed releases.json content (dict) or None if not found
        """
        assets = gh_release.get("assets", [])
        
        # Find releases.json asset
        metadata_asset = None
        for asset in assets:
            if asset.get("name") == "releases.json":
                metadata_asset = asset
                break
        
        if not metadata_asset:
            return None
        
        # For private repos, use API endpoint instead of browser_download_url
        asset_id = metadata_asset.get("id")
        asset_url = metadata_asset.get("url")  # API URL, not browser URL
        
        if not asset_url:
            return None
        
        try:
            request = self._create_request(
                asset_url,
                accept_header="application/octet-stream"
            )
            with urlopen(request, timeout=self.TIMEOUT_SECONDS) as response:
                content = response.read().decode()
                return json.loads(content)
        
        except (URLError, HTTPError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to download asset {asset_id}: {e}")
            return None
    
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
