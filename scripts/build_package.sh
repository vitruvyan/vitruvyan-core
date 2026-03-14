#!/usr/bin/env bash
# build_package.sh — Build a .vit.tar.gz tarball from a local manifest
#
# Usage:
#   ./scripts/build_package.sh service-edge-oculus-prime
#   ./scripts/build_package.sh service-neural-engine
#   ./scripts/build_package.sh --all
#
# Output:  dist/<package_name>-<version>.vit.tar.gz
#          dist/<package_name>-<version>.sha256
#
# The tarball contains:
#   manifest.vit      — the package manifest (renamed for consistency)
#   <original>.vit     — original file preserved
#
# For services that ship with vitruvyan-core, that's sufficient.
# The Dockerfile / compose_file paths in the manifest point to the
# local repo, so `vit install` can run `docker compose up` directly.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFESTS_DIR="$REPO_ROOT/vitruvyan_core/core/platform/package_manager/packages/manifests"
DIST_DIR="$REPO_ROOT/dist"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}  ✓${NC} $*"; }
warn()  { echo -e "${YELLOW}  ⚠${NC} $*"; }
error() { echo -e "${RED}  ✗${NC} $*" >&2; }

usage() {
    echo "Usage: $0 <package-name> | --all"
    echo ""
    echo "  Build .vit.tar.gz packages from local manifests."
    echo ""
    echo "  Examples:"
    echo "    $0 service-edge-oculus-prime"
    echo "    $0 service-neural-engine"
    echo "    $0 --all    # build all non-template manifests"
    echo ""
    echo "  Output: dist/<package>-<version>.vit.tar.gz"
    exit 1
}

# Extract a YAML value (simple grep-based, no yq dependency)
yaml_val() {
    local file="$1" key="$2"
    grep "^${key}:" "$file" | head -1 | sed "s/^${key}:[[:space:]]*//" | tr -d '"' | tr -d "'"
}

build_package() {
    local manifest_file="$1"
    local basename
    basename="$(basename "$manifest_file" .vit)"

    local pkg_name pkg_version
    pkg_name="$(yaml_val "$manifest_file" "package_name")"
    pkg_version="$(yaml_val "$manifest_file" "package_version")"

    if [[ -z "$pkg_name" || -z "$pkg_version" ]]; then
        error "Could not parse package_name/package_version from $manifest_file"
        return 1
    fi

    # Skip template
    if [[ "$pkg_name" == *"<"* || "$pkg_name" == *"DOMAIN"* ]]; then
        warn "Skipping template: $basename"
        return 0
    fi

    local tarball_name="${pkg_name}-${pkg_version}.vit.tar.gz"
    local sha_name="${pkg_name}-${pkg_version}.sha256"
    local tarball_path="$DIST_DIR/$tarball_name"
    local sha_path="$DIST_DIR/$sha_name"

    mkdir -p "$DIST_DIR"

    # Build tarball in a temp directory
    local tmpdir
    tmpdir="$(mktemp -d)"
    trap "rm -rf '$tmpdir'" RETURN

    # Copy manifest as both manifest.vit and original name
    cp "$manifest_file" "$tmpdir/manifest.vit"
    cp "$manifest_file" "$tmpdir/${basename}.vit"

    # Create tarball
    tar -czf "$tarball_path" -C "$tmpdir" .

    # Compute SHA-256
    sha256sum "$tarball_path" | awk '{print $1}' > "$sha_path"
    local checksum
    checksum="$(cat "$sha_path")"

    info "$pkg_name v$pkg_version → $tarball_name"
    info "  SHA-256: ${checksum:0:16}..."
    info "  Size: $(du -h "$tarball_path" | cut -f1)"

    # Print registry.json snippet for convenience
    echo ""
    echo "  Registry entry:"
    echo "    \"$pkg_name\": {"
    echo "      \"latest\": \"$pkg_version\","
    echo "      \"versions\": {"
    echo "        \"$pkg_version\": {"
    echo "          \"release_tag\": \"${pkg_name}-v${pkg_version}\","
    echo "          \"asset\": \"$tarball_name\","
    echo "          \"sha256\": \"$checksum\""
    echo "        }"
    echo "      }"
    echo "    }"
    echo ""
}

# ── Main ─────────────────────────────────────────────────────────────

if [[ $# -lt 1 ]]; then
    usage
fi

echo ""
echo "  Vitruvyan Package Builder"
echo "  ─────────────────────────"
echo ""

if [[ "$1" == "--all" ]]; then
    count=0
    for vit_file in "$MANIFESTS_DIR"/*.vit; do
        [[ -f "$vit_file" ]] || continue
        build_package "$vit_file"
        ((count++)) || true
    done
    echo ""
    info "Built $count packages → $DIST_DIR/"
else
    # Find manifest by name
    pkg="$1"
    manifest=""

    # Try exact match first
    if [[ -f "$MANIFESTS_DIR/${pkg}.vit" ]]; then
        manifest="$MANIFESTS_DIR/${pkg}.vit"
    else
        # Search by package_name in .vit files
        for vit_file in "$MANIFESTS_DIR"/*.vit; do
            [[ -f "$vit_file" ]] || continue
            name="$(yaml_val "$vit_file" "package_name")"
            if [[ "$name" == "$pkg" ]]; then
                manifest="$vit_file"
                break
            fi
        done
    fi

    if [[ -z "$manifest" ]]; then
        error "Manifest not found for '$pkg'"
        echo ""
        echo "  Available manifests:"
        for vit_file in "$MANIFESTS_DIR"/*.vit; do
            [[ -f "$vit_file" ]] || continue
            name="$(yaml_val "$vit_file" "package_name")"
            echo "    - $name"
        done
        exit 1
    fi

    build_package "$manifest"
fi
