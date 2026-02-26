#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
FEDERATE_SCRIPT="${SCRIPT_DIR}/federate_docs.py"

BUNDLE_PATH=""
DRY_RUN=0
CORE_ROOT="docs/knowledge_base/federated/core"
VERTICAL_ROOT="docs/knowledge_base/federated/verticals"

usage() {
  cat <<'EOF'
Usage:
  scripts/docs/ingest_incoming_bundle.sh --bundle <bundle.tar.gz> [options]

Options:
  --bundle <path>                  Required.
  --repo-root <path>               Repository root (default: autodetected).
  --core-root <path>               Core routing root.
  --vertical-root <path>           Vertical routing root.
  --dry-run                        Print actions without writing files.
  -h|--help                        Show help.

Environment:
  DOCS_KB_INGEST_CMD               Optional hook executed after successful ingest.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bundle) BUNDLE_PATH="${2:-}"; shift 2 ;;
    --repo-root) REPO_ROOT="${2:-}"; shift 2 ;;
    --core-root) CORE_ROOT="${2:-}"; shift 2 ;;
    --vertical-root) VERTICAL_ROOT="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "${BUNDLE_PATH}" ]]; then
  echo "--bundle is required." >&2
  usage
  exit 1
fi

cmd=(
  python3 "${FEDERATE_SCRIPT}" ingest
  --bundle "${BUNDLE_PATH}"
  --repo-root "${REPO_ROOT}"
  --core-root "${CORE_ROOT}"
  --vertical-root "${VERTICAL_ROOT}"
)

if [[ "${DRY_RUN}" -eq 1 ]]; then
  cmd+=(--dry-run)
fi

echo "Ingesting bundle..."
"${cmd[@]}"

if [[ -n "${DOCS_KB_INGEST_CMD:-}" ]]; then
  echo "DOCS_KB_INGEST_CMD was provided and handled by federate_docs.py."
fi
