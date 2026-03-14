"""
Remote Package Registry — fetch packages from vitruvyan-packages on GitHub.

Flow:
  1. Fetch registry.json from GitHub (raw content)
  2. Resolve package version
  3. Download .vit.tar.gz from GitHub Release assets
  4. Verify SHA-256 checksum
  5. Extract to .vitruvyan/packages/<name>-<version>/
  6. Return local PackageManifest from extracted manifest.vit

License validation for premium packages is handled at download time.
Community packages download directly from GitHub (no auth proxy).
"""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from .models import PackageManifest

logger = logging.getLogger(__name__)

# Registry source — raw GitHub content (no API rate limits for public repos)
REGISTRY_URL = (
    "https://raw.githubusercontent.com/vitruvyan/vitruvyan-packages/main/registry.json"
)
RELEASE_BASE_URL = (
    "https://github.com/vitruvyan/vitruvyan-packages/releases/download"
)

# Can be overridden via env var for self-hosted registries
REGISTRY_URL_ENV = "VIT_REGISTRY_URL"
RELEASE_BASE_URL_ENV = "VIT_RELEASE_BASE_URL"

# License proxy for premium packages
LICENSE_PROXY_URL_ENV = "VIT_LICENSE_PROXY_URL"


class RemoteRegistry:
    """
    Fetch and cache the remote package registry.

    Usage:
        remote = RemoteRegistry()
        index = remote.fetch_index()
        pkg = remote.get_package("frontier-odoo")
        versions = remote.get_versions("oculus-prime")
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self._cache_dir = cache_dir or self._find_cache_dir()
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_file = self._cache_dir / "registry_cache.json"
        self._index: Optional[dict] = None

    @staticmethod
    def _find_cache_dir() -> Path:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, check=True, timeout=5,
            )
            return Path(result.stdout.strip()) / ".vitruvyan" / "cache"
        except Exception:
            return Path.home() / ".vitruvyan" / "cache"

    def fetch_index(self, force: bool = False) -> dict:
        """
        Fetch registry.json from remote. Uses local cache if fresh (< 1 hour).
        """
        if self._index and not force:
            return self._index

        # Check cache freshness
        if not force and self._cache_file.exists():
            import time
            age = time.time() - self._cache_file.stat().st_mtime
            if age < 3600:  # 1 hour cache
                try:
                    with open(self._cache_file, "r") as f:
                        self._index = json.load(f)
                    logger.debug("Using cached registry (age: %ds)", int(age))
                    return self._index
                except (json.JSONDecodeError, OSError):
                    pass

        # Fetch from remote
        registry_url = os.environ.get(REGISTRY_URL_ENV, REGISTRY_URL)
        logger.info("Fetching remote registry from %s", registry_url)

        try:
            req = Request(registry_url, headers={"User-Agent": "vit-cli/1.0"})
            with urlopen(req, timeout=15) as resp:
                data = resp.read().decode("utf-8")
                self._index = json.loads(data)
        except (URLError, HTTPError, json.JSONDecodeError) as e:
            logger.warning("Failed to fetch remote registry: %s", e)
            # Fall back to cache even if stale
            if self._cache_file.exists():
                with open(self._cache_file, "r") as f:
                    self._index = json.load(f)
                logger.info("Using stale cache as fallback")
                return self._index
            raise RuntimeError(f"Cannot reach remote registry: {e}") from e

        # Update cache
        try:
            with open(self._cache_file, "w") as f:
                json.dump(self._index, f, indent=2)
        except OSError as e:
            logger.warning("Failed to cache registry: %s", e)

        return self._index

    def get_package(self, name: str) -> Optional[dict]:
        """Lookup a package in the remote registry."""
        index = self.fetch_index()
        packages = index.get("packages", {})
        return packages.get(name)

    def get_versions(self, name: str) -> Dict[str, dict]:
        """Get all published versions of a package."""
        pkg = self.get_package(name)
        if not pkg:
            return {}
        return pkg.get("versions", {})

    def list_packages(self) -> List[dict]:
        """List all packages in the remote registry."""
        index = self.fetch_index()
        packages = index.get("packages", {})
        result = []
        for name, info in packages.items():
            result.append({"name": name, **info})
        return result

    def search(self, query: str) -> List[dict]:
        """Search remote packages by name or description."""
        query_lower = query.lower()
        results = []
        for pkg in self.list_packages():
            if (
                query_lower in pkg["name"].lower()
                or query_lower in pkg.get("description", "").lower()
                or query_lower in pkg.get("display_name", "").lower()
            ):
                results.append(pkg)
        return results

    def has_published_versions(self, name: str) -> bool:
        """Check if a package has any published versions."""
        versions = self.get_versions(name)
        return len(versions) > 0


class PackageDownloader:
    """
    Download and extract remote packages.

    Usage:
        downloader = PackageDownloader()
        manifest = downloader.download_and_extract("oculus-prime", "1.0.0", pkg_info)
    """

    def __init__(self, packages_dir: Optional[Path] = None):
        self._packages_dir = packages_dir or self._find_packages_dir()
        self._packages_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _find_packages_dir() -> Path:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, check=True, timeout=5,
            )
            return Path(result.stdout.strip()) / ".vitruvyan" / "packages"
        except Exception:
            return Path.home() / ".vitruvyan" / "packages"

    def download_and_extract(
        self,
        package_name: str,
        version: str,
        version_info: dict,
        license_token: Optional[str] = None,
    ) -> Path:
        """
        Download a package tarball, verify checksum, and extract.

        Args:
            package_name: e.g. "oculus-prime"
            version: e.g. "1.0.0"
            version_info: dict from registry (asset, sha256, release_tag, etc.)
            license_token: required for premium packages

        Returns:
            Path to extracted package directory.

        Raises:
            RuntimeError: on download/checksum/extraction failure.
        """
        asset_name = version_info["asset"]
        release_tag = version_info["release_tag"]
        expected_sha256 = version_info.get("sha256")

        extract_dir = self._packages_dir / f"{package_name}-{version}"

        # Already extracted?
        manifest_path = extract_dir / "manifest.vit"
        if manifest_path.exists():
            logger.info("Package already extracted: %s", extract_dir)
            return extract_dir

        # Build download URL
        base_url = os.environ.get(RELEASE_BASE_URL_ENV, RELEASE_BASE_URL)
        download_url = f"{base_url}/{release_tag}/{asset_name}"

        # Premium packages: use license proxy
        license_proxy = os.environ.get(LICENSE_PROXY_URL_ENV)
        headers = {"User-Agent": "vit-cli/1.0"}

        if license_token:
            if license_proxy:
                download_url = f"{license_proxy}/v1/download/{package_name}/{version}"
            headers["Authorization"] = f"Bearer {license_token}"

        logger.info("Downloading %s v%s from %s", package_name, version, download_url)

        # Download to temp file
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                req = Request(download_url, headers=headers)
                with urlopen(req, timeout=120) as resp:
                    shutil.copyfileobj(resp, tmp)
            except HTTPError as e:
                tmp_path.unlink(missing_ok=True)
                if e.code == 401:
                    raise RuntimeError(
                        f"License required for {package_name}. "
                        f"Set your license in .vitruvyan/license.key"
                    ) from e
                if e.code == 403:
                    raise RuntimeError(
                        f"License invalid or expired for {package_name}."
                    ) from e
                raise RuntimeError(f"Download failed: HTTP {e.code}") from e
            except URLError as e:
                tmp_path.unlink(missing_ok=True)
                raise RuntimeError(f"Download failed: {e}") from e

        # Verify checksum
        if expected_sha256:
            actual_sha256 = self._sha256(tmp_path)
            if actual_sha256 != expected_sha256:
                tmp_path.unlink(missing_ok=True)
                raise RuntimeError(
                    f"Checksum mismatch for {asset_name}: "
                    f"expected {expected_sha256}, got {actual_sha256}"
                )
            logger.info("Checksum verified: %s", expected_sha256[:16])

        # Extract
        extract_dir.mkdir(parents=True, exist_ok=True)
        try:
            with tarfile.open(tmp_path, "r:gz") as tar:
                # Security: prevent path traversal
                for member in tar.getmembers():
                    member_path = Path(member.name)
                    if member_path.is_absolute() or ".." in member_path.parts:
                        raise RuntimeError(
                            f"Unsafe path in tarball: {member.name}"
                        )
                tar.extractall(path=extract_dir)
        except (tarfile.TarError, RuntimeError) as e:
            shutil.rmtree(extract_dir, ignore_errors=True)
            raise RuntimeError(f"Extraction failed: {e}") from e
        finally:
            tmp_path.unlink(missing_ok=True)

        logger.info("Extracted to %s", extract_dir)
        return extract_dir

    @staticmethod
    def _sha256(path: Path) -> str:
        """Compute SHA-256 hex digest of a file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def get_extracted_dir(self, package_name: str, version: str) -> Optional[Path]:
        """Get path to already-extracted package, or None."""
        extract_dir = self._packages_dir / f"{package_name}-{version}"
        if (extract_dir / "manifest.vit").exists():
            return extract_dir
        return None

    def cleanup(self, package_name: str, version: str):
        """Remove extracted package files."""
        extract_dir = self._packages_dir / f"{package_name}-{version}"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
            logger.info("Cleaned up %s", extract_dir)


def read_license_token() -> Optional[str]:
    """
    Read license token from .vitruvyan/license.key or VIT_LICENSE_TOKEN env var.
    """
    # Env var takes precedence
    token = os.environ.get("VIT_LICENSE_TOKEN")
    if token:
        return token.strip()

    # File-based
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True, timeout=5,
        )
        license_file = Path(result.stdout.strip()) / ".vitruvyan" / "license.key"
    except Exception:
        license_file = Path.home() / ".vitruvyan" / "license.key"

    if license_file.exists():
        return license_file.read_text().strip()

    return None
