#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
FEDERATE_SCRIPT="${SCRIPT_DIR}/federate_docs.py"

SCOPE=""
PRODUCER=""
VERTICAL=""
SOURCE_DIR="docs"
OUTPUT_DIR="${REPO_ROOT}/tmp/docs_federation_out"
OUTPUT_BUNDLE=""
HUB_HOST=""
HUB_USER=""
HUB_PATH=""
DRY_RUN=0
SKIP_TRANSFER=0

usage() {
  cat <<'EOF'
Usage:
  scripts/docs/publish_docs.sh --scope <core|vertical> --producer <id> [options]

Options:
  --scope <core|vertical>          Required.
  --producer <producer-id>         Required.
  --vertical <vertical-id>         Required when scope=vertical.
  --source <dir>                   Source docs directory (default: docs).
  --output-dir <dir>               Output directory for bundle.
  --output-bundle <path>           Full output bundle path.
  --hub-host <host>                Optional hub host for scp transfer.
  --hub-user <user>                Optional hub SSH user.
  --hub-path <remote-path>         Optional remote path for scp.
  --skip-transfer                  Build bundle only.
  --dry-run                        Print actions without side effects.
  -h|--help                        Show help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope) SCOPE="${2:-}"; shift 2 ;;
    --producer) PRODUCER="${2:-}"; shift 2 ;;
    --vertical) VERTICAL="${2:-}"; shift 2 ;;
    --source) SOURCE_DIR="${2:-}"; shift 2 ;;
    --output-dir) OUTPUT_DIR="${2:-}"; shift 2 ;;
    --output-bundle) OUTPUT_BUNDLE="${2:-}"; shift 2 ;;
    --hub-host) HUB_HOST="${2:-}"; shift 2 ;;
    --hub-user) HUB_USER="${2:-}"; shift 2 ;;
    --hub-path) HUB_PATH="${2:-}"; shift 2 ;;
    --skip-transfer) SKIP_TRANSFER=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "${SCOPE}" || -z "${PRODUCER}" ]]; then
  echo "--scope and --producer are required." >&2
  usage
  exit 1
fi

if [[ "${SCOPE}" == "vertical" && -z "${VERTICAL}" ]]; then
  echo "--vertical is required when --scope=vertical." >&2
  exit 1
fi

SOURCE_COMMIT="${DOCS_SOURCE_COMMIT:-$(git -C "${REPO_ROOT}" rev-parse --short HEAD 2>/dev/null || true)}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"

if [[ -z "${OUTPUT_BUNDLE}" ]]; then
  mkdir -p "${OUTPUT_DIR}"
  OUTPUT_BUNDLE="${OUTPUT_DIR}/${PRODUCER}_${SCOPE}_${TIMESTAMP}.tar.gz"
fi

bundle_cmd=(
  python3 "${FEDERATE_SCRIPT}" bundle
  --scope "${SCOPE}"
  --producer "${PRODUCER}"
  --source "${SOURCE_DIR}"
  --output "${OUTPUT_BUNDLE}"
)

if [[ -n "${VERTICAL}" ]]; then
  bundle_cmd+=(--vertical "${VERTICAL}")
fi
if [[ -n "${SOURCE_COMMIT}" ]]; then
  bundle_cmd+=(--source-commit "${SOURCE_COMMIT}")
fi
if [[ "${DRY_RUN}" -eq 1 ]]; then
  bundle_cmd+=(--dry-run)
fi

echo "Building docs bundle..."
"${bundle_cmd[@]}"

if [[ "${SKIP_TRANSFER}" -eq 1 ]]; then
  echo "Transfer skipped (--skip-transfer)."
  exit 0
fi

if [[ -n "${HUB_HOST}" && -n "${HUB_PATH}" ]]; then
  target="${HUB_HOST}:${HUB_PATH}"
  if [[ -n "${HUB_USER}" ]]; then
    target="${HUB_USER}@${target}"
  fi

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "Dry-run: would transfer ${OUTPUT_BUNDLE} -> ${target}"
  else
    echo "Transferring bundle via scp..."
    scp "${OUTPUT_BUNDLE}" "${target}"
  fi
else
  echo "No --hub-host/--hub-path provided, transfer step skipped."
fi

echo "Next step on hub:"
echo "  scripts/docs/ingest_incoming_bundle.sh --bundle <path-on-hub>"
