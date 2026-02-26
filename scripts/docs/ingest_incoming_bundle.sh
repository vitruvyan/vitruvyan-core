#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <bundle.tar.gz>"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUNDLE_PATH="$1"

if [[ ! -f "$BUNDLE_PATH" ]]; then
  echo "Bundle not found: $BUNDLE_PATH"
  exit 1
fi

python3 "$ROOT_DIR/scripts/docs/federate_docs.py" ingest \
  --repo-root "$ROOT_DIR" \
  --bundle "$BUNDLE_PATH" \
  --update-mkdocs-nav

# Optional MkDocs build
# DOCS_BUILD_MKDOCS=true (default) triggers local build if mkdocs exists.
DOCS_BUILD_MKDOCS="${DOCS_BUILD_MKDOCS:-true}"
if [[ "$DOCS_BUILD_MKDOCS" == "true" ]]; then
  if command -v mkdocs >/dev/null 2>&1; then
    mkdocs build -f "$ROOT_DIR/infrastructure/docker/mkdocs/mkdocs.yml"
  else
    echo "mkdocs command not found, skipping build"
  fi
fi

# Optional KB ingestion command (for vector indexing pipeline).
# Example:
# export DOCS_KB_INGEST_CMD="python3 /opt/vitruvyan-core/scripts/kb/ingest_docs.py"
if [[ -n "${DOCS_KB_INGEST_CMD:-}" ]]; then
  bash -lc "$DOCS_KB_INGEST_CMD"
fi

echo "ingest_completed bundle=$BUNDLE_PATH"
