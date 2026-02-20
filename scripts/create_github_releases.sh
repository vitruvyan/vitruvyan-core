#!/usr/bin/env bash
# Create GitHub Releases from existing Git tags
# Requires: GITHUB_TOKEN environment variable

set -e

REPO="dbaldoni/vitruvyan-core"
GITHUB_API="https://api.github.com"

# Check GITHUB_TOKEN
if [[ -z "${GITHUB_TOKEN}" ]]; then
    echo "❌ Error: GITHUB_TOKEN environment variable not set"
    echo ""
    echo "Create a token at: https://github.com/settings/tokens"
    echo "Required scopes: repo (Full control of private repositories)"
    echo ""
    echo "Usage:"
    echo "  export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx"
    echo "  ./scripts/create_github_releases.sh"
    exit 1
fi

echo "🚀 Creating GitHub Releases for ${REPO}"
echo ""

# Release v1.2.0
echo "📦 Creating release v1.2.0..."
curl -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  "${GITHUB_API}/repos/${REPO}/releases" \
  -d '{
    "tag_name": "v1.2.0",
    "name": "v1.2.0 - Update Manager System + Complete Pipeline Visualization",
    "body": "## 🎯 MAJOR FEATURES\n\n- **Update Manager System** with vit CLI (update/upgrade/rollback/status)\n- **Complete Intake→Vault pipeline visualization** (interactive Mermaid)\n- **Vertical Implementation Guides** (IT/EN with LangGraph integration)\n- **MkDocs multi-build** (public/docs/admin at ports 9800/9801/9802)\n\n## 📦 CONTRACTS & COMPLIANCE\n\n- PACKAGE_MANAGER_SYSTEM_CONTRACT_V1\n- UPDATE_SYSTEM_CONTRACT_V1\n- Vertical Contract V1 + Conformance Checklist\n\n## 🔧 INFRASTRUCTURE\n\n- LangGraph 1.0.8 in production\n- Sacred Orders PATTERN conformance\n- Legacy cleanup (test containers removed)\n\n## 🧪 TESTING\n\n- CI/CD integration with pytest\n- Notification system (desktop/webhook/log)\n- Contract validation gates\n\n## 📊 COMMITS\n\n8 commits (2026-02-12 to 2026-02-20)\n\n## 🎯 For Testing\n\nEnable update manager testing on remote instances.",
    "draft": false,
    "prerelease": false
  }'
echo ""
echo "✅ v1.2.0 created"
echo ""

# Release v1.2.1
echo "📦 Creating release v1.2.1..."
curl -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  "${GITHUB_API}/repos/${REPO}/releases" \
  -d '{
    "tag_name": "v1.2.1",
    "name": "v1.2.1 - Out-of-the-Box CLI (Critical Fix)",
    "body": "## 🎯 CRITICAL IMPROVEMENT\n\nvit CLI now works **IMMEDIATELY** after git clone without any installation:\n\n```bash\ngit clone https://github.com/dbaldoni/vitruvyan-core.git\ncd vitruvyan-core\n./vit status    # WORKS INSTANTLY!\n```\n\n## ✨ NEW FEATURES\n\n- **Executable vit wrapper script** (repo root, auto-configures PYTHONPATH)\n- **Auto-setup autocomplete** on first interactive run (prompts user)\n- **VIT_CLI_QUICKSTART.md** comprehensive quick start guide\n- **README.md integrated** Update Manager CLI section\n\n## 🔧 DESIGN PHILOSOPHY\n\nUpdate Manager is an **INTEGRAL PART** of vitruvyan-core.\n\n- ✅ Zero external dependencies\n- ✅ Zero installation steps\n- ✅ Zero friction\n\n## 📦 USAGE (Zero Setup Required)\n\n```bash\ngit clone https://github.com/dbaldoni/vitruvyan-core.git\ncd vitruvyan-core\n./vit status    # WORKS!\n```\n\n## 🚀 TESTING\n\nPerfect for remote instance deployment testing.\nPull v1.2.1, vit works out-of-the-box.\n\n## 📊 COMMITS\n\n2 commits since v1.2.0 (critical usability fix)",
    "draft": false,
    "prerelease": false,
    "make_latest": "true"
  }'
echo ""
echo "✅ v1.2.1 created (marked as latest)"
echo ""

echo "🎉 GitHub Releases created successfully!"
echo ""
echo "Verify at: https://github.com/${REPO}/releases"
