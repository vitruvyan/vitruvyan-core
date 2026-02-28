#!/usr/bin/env bash
set -euo pipefail

# Producer-side publisher.
# 1) Build docs bundle with metadata manifest
# 2) Optionally ship bundle to hub VPS and trigger ingestion

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

DOCS_SOURCE_REPO="${DOCS_SOURCE_REPO:-$(basename "$ROOT_DIR")}"
DOCS_SOURCE_VPS="${DOCS_SOURCE_VPS:-$(hostname -f 2>/dev/null || hostname)}"
DOCS_DEFAULT_SCOPE="${DOCS_DEFAULT_SCOPE:-vertical}"
DOCS_DEFAULT_VERTICAL="${DOCS_DEFAULT_VERTICAL:-${DOCS_SOURCE_REPO}}"
DOCS_BASE_REF="${DOCS_BASE_REF:-origin/main}"
DOCS_CHANGED_ONLY="${DOCS_CHANGED_ONLY:-true}"
DOCS_INCLUDE_UNCOMMITTED="${DOCS_INCLUDE_UNCOMMITTED:-false}"
DOCS_BUNDLE_OUT="${DOCS_BUNDLE_OUT:-/tmp/${DOCS_SOURCE_REPO}_docs_bundle_$(date +%Y%m%d_%H%M%S).tar.gz}"

ARGS=(
  bundle
  --repo-root "$ROOT_DIR"
  --output "$DOCS_BUNDLE_OUT"
  --base-ref "$DOCS_BASE_REF"
  --default-scope "$DOCS_DEFAULT_SCOPE"
  --default-vertical "$DOCS_DEFAULT_VERTICAL"
  --source-repo "$DOCS_SOURCE_REPO"
  --source-vps "$DOCS_SOURCE_VPS"
)

if [[ "$DOCS_CHANGED_ONLY" == "true" ]]; then
  ARGS+=(--changed-only)
fi
if [[ "$DOCS_INCLUDE_UNCOMMITTED" == "true" ]]; then
  ARGS+=(--include-uncommitted)
fi

python3 "$ROOT_DIR/scripts/docs/federate_docs.py" "${ARGS[@]}"
echo "docs_bundle=$DOCS_BUNDLE_OUT"

# Optional remote handoff (hub VPS)
# Required env to enable:
# - DOCS_HUB_SSH_TARGET: e.g. docs-sync@144.xxx.xxx.xxx
# Optional:
# - DOCS_HUB_DROP_DIR (default /opt/vitruvyan-core/incoming_docs)
# - DOCS_HUB_INGEST_CMD (default /opt/vitruvyan-core/scripts/docs/ingest_incoming_bundle.sh)
if [[ -n "${DOCS_HUB_SSH_TARGET:-}" ]]; then
  DOCS_HUB_DROP_DIR="${DOCS_HUB_DROP_DIR:-/opt/vitruvyan-core/incoming_docs}"
  DOCS_HUB_INGEST_CMD="${DOCS_HUB_INGEST_CMD:-/opt/vitruvyan-core/scripts/docs/ingest_incoming_bundle.sh}"
  REMOTE_BUNDLE_PATH="$DOCS_HUB_DROP_DIR/$(basename "$DOCS_BUNDLE_OUT")"

  echo "shipping_bundle_to=$DOCS_HUB_SSH_TARGET:$REMOTE_BUNDLE_PATH"
  ssh "$DOCS_HUB_SSH_TARGET" "mkdir -p '$DOCS_HUB_DROP_DIR'"
  scp "$DOCS_BUNDLE_OUT" "$DOCS_HUB_SSH_TARGET:$REMOTE_BUNDLE_PATH"
  ssh "$DOCS_HUB_SSH_TARGET" "$DOCS_HUB_INGEST_CMD '$REMOTE_BUNDLE_PATH'"
fi
