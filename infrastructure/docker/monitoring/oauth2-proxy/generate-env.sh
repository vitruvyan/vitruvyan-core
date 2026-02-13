#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${DIR}/oauth2-proxy.env"

KEYCLOAK_ENV="${DIR}/../../keycloak/keycloak.env"

if [[ -f "${ENV_FILE}" ]]; then
  # Ensure cookie secret length is valid for oauth2-proxy (16/24/32 bytes).
  COOKIE_SECRET="$(grep -E '^OAUTH2_PROXY_COOKIE_SECRET=' "${ENV_FILE}" | head -n 1 | cut -d= -f2- || true)"
  if [[ "${#COOKIE_SECRET}" == "16" || "${#COOKIE_SECRET}" == "24" || "${#COOKIE_SECRET}" == "32" ]]; then
    echo "OK: ${ENV_FILE} already exists."
    exit 0
  fi
  echo "WARN: existing cookie secret has invalid length (${#COOKIE_SECRET}); regenerating file."
  rm -f "${ENV_FILE}"
fi

if [[ ! -f "${KEYCLOAK_ENV}" ]]; then
  echo "ERROR: missing ${KEYCLOAK_ENV}. Run infrastructure/docker/keycloak/generate-env.sh first."
  exit 1
fi

CLIENT_SECRET="$(grep -E '^KB_OIDC_CLIENT_SECRET=' "${KEYCLOAK_ENV}" | head -n 1 | cut -d= -f2- || true)"
if [[ -z "${CLIENT_SECRET}" ]]; then
  echo "ERROR: KB_OIDC_CLIENT_SECRET not found in ${KEYCLOAK_ENV}."
  exit 1
fi

umask 077

# 32 ASCII chars -> 32 bytes (valid for AES-256 cookie cipher)
COOKIE_SECRET="$(openssl rand -hex 16)"

cat >"${ENV_FILE}" <<EOF
OAUTH2_PROXY_CLIENT_SECRET=${CLIENT_SECRET}
OAUTH2_PROXY_COOKIE_SECRET=${COOKIE_SECRET}
EOF

echo "OK: wrote ${ENV_FILE} (mode 600)."
