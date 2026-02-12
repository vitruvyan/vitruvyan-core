#!/bin/bash
# ============================================================================
# MkDocs Multi-Build Script — Public + Full Documentation
# ============================================================================
# Purpose: Build two separate documentation sites with different access levels
# Usage:   ./build-all.sh
# Output:  /app/site_public (no auth) + /app/site (authenticated)
# ============================================================================

set -e  # Exit on error

echo "🏗️  Building Vitruvyan Knowledge Base (Multi-Build)..."
echo ""

# Build 1: Public documentation (no authentication required)
echo "📚 [1/2] Building PUBLIC documentation..."
mkdocs build \
  --config-file /app/mkdocs.public.yml \
  --site-dir /app/site_public \
  --clean

echo "✅ Public site: /app/site_public"
echo ""

# Build 2: Full documentation (authentication required)
echo "📚 [2/2] Building FULL documentation..."
mkdocs build \
  --config-file /app/mkdocs.yml \
  --site-dir /app/site \
  --clean

echo "✅ Full site: /app/site"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Multi-build complete!"
echo ""
echo "PUBLIC:  $(du -sh /app/site_public | cut -f1) (no auth)"
echo "FULL:    $(du -sh /app/site | cut -f1) (authenticated)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
