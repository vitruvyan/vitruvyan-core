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

# Cleanup legacy i18n filenames/symlinks (avoid conflicts with mkdocs-static-i18n)
rm -f /app/docs_root/index.en.md 2>/dev/null || true

# Prepare public landing page (single file only)
echo "📄 Preparing public landing page..."
cp /app/docs/public/landing.md /app/docs_root_public/index.md
echo "✅ Copied landing.md → docs_root_public/index.md"

if [ -f /app/docs/public/landing.it.md ]; then
  cp /app/docs/public/landing.it.md /app/docs_root_public/index.it.md
  echo "✅ Copied landing.it.md → docs_root_public/index.it.md"
fi

# Shared assets (stylesheets, images, etc.) used by public landing
mkdir -p /app/docs_root_public/docs/stylesheets
mkdir -p /app/docs_root_public/docs/javascripts
mkdir -p /app/docs_root_public/assets/kb
if [ -f /app/docs/stylesheets/vitruvyan.css ]; then
  cp /app/docs/stylesheets/vitruvyan.css /app/docs_root_public/docs/stylesheets/vitruvyan.css
  cp /app/docs/stylesheets/vitruvyan.css /app/docs_root_public/assets/kb/vitruvyan.css
  echo "✅ Copied vitruvyan.css → docs_root_public/docs/stylesheets/vitruvyan.css"
fi
if [ -f /app/docs/stylesheets/material_v1.css ]; then
  cp /app/docs/stylesheets/material_v1.css /app/docs_root_public/docs/stylesheets/material_v1.css
  cp /app/docs/stylesheets/material_v1.css /app/docs_root_public/assets/kb/material_v1.css
  echo "✅ Copied material_v1.css → docs_root_public/docs/stylesheets/material_v1.css"
fi
if [ -f /app/docs/stylesheets/vitruvyan-logo-white.png ]; then
  cp /app/docs/stylesheets/vitruvyan-logo-white.png /app/docs_root_public/docs/stylesheets/vitruvyan-logo-white.png
  cp /app/docs/stylesheets/vitruvyan-logo-white.png /app/docs_root_public/assets/kb/vitruvyan-logo-white.png
  echo "✅ Copied vitruvyan-logo-white.png → public stylesheets/assets"
fi
if [ -f /app/docs/stylesheets/vitruvyan-logo-white-hover.png ]; then
  cp /app/docs/stylesheets/vitruvyan-logo-white-hover.png /app/docs_root_public/docs/stylesheets/vitruvyan-logo-white-hover.png
  cp /app/docs/stylesheets/vitruvyan-logo-white-hover.png /app/docs_root_public/assets/kb/vitruvyan-logo-white-hover.png
  echo "✅ Copied vitruvyan-logo-white-hover.png → public stylesheets/assets"
fi
if [ -f /app/docs/assets/images/vitruvyan-logo.png ]; then
  cp /app/docs/assets/images/vitruvyan-logo.png /app/docs_root_public/assets/kb/vitruvyan-logo.png
  echo "✅ Copied vitruvyan-logo.png → docs_root_public/assets/kb/vitruvyan-logo.png"
fi
if [ -f /app/docs/javascripts/vitruvyan.js ]; then
  cp /app/docs/javascripts/vitruvyan.js /app/docs_root_public/docs/javascripts/vitruvyan.js
  cp /app/docs/javascripts/vitruvyan.js /app/docs_root_public/assets/kb/vitruvyan.js
  echo "✅ Copied vitruvyan.js → docs_root_public/docs/javascripts/vitruvyan.js"
fi
echo ""

# Build 1: Public documentation (no authentication required)
echo "📚 [1/2] Building PUBLIC documentation..."
mkdocs build \
  --config-file /app/mkdocs.public.yml \
  --site-dir /app/site_public \
  --clean

echo "✅ Public site: /app/site_public"
echo ""

# Build 2: Public KB documentation (no authentication)
echo "📚 [2/3] Building PUBLIC KB documentation..."
mkdocs build \
  --config-file /app/mkdocs.docs.yml \
  --site-dir /app/site_docs_public \
  --clean

echo "✅ Public docs site: /app/site_docs_public"
echo ""

# Build 3: Admin documentation (authentication required)
echo "📚 [3/3] Building ADMIN documentation..."
mkdocs build \
  --config-file /app/mkdocs.yml \
  --site-dir /app/site \
  --clean

echo "✅ Admin site: /app/site"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Multi-build complete!"
echo ""
echo "PUBLIC:  $(du -sh /app/site_public | cut -f1) (no auth)"
echo "DOCS:    $(du -sh /app/site_docs_public | cut -f1) (no auth)"
echo "ADMIN:   $(du -sh /app/site | cut -f1) (authenticated)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
