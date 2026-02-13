#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${DIR}/keycloak.env"

umask 077

rand_b64() {
  # 32 bytes -> 44 chars base64
  openssl rand -base64 32
}

ensure_line() {
  local key="$1"
  local value="$2"
  if grep -Eq "^${key}=" "${ENV_FILE}" 2>/dev/null; then
    return 0
  fi
  echo "${key}=${value}" >>"${ENV_FILE}"
}

if [[ ! -f "${ENV_FILE}" ]]; then
  : >"${ENV_FILE}"
fi

KC_DB_PASSWORD="$(grep -E '^KC_DB_PASSWORD=' "${ENV_FILE}" | head -n 1 | cut -d= -f2- || true)"
if [[ -z "${KC_DB_PASSWORD}" ]]; then
  KC_DB_PASSWORD="$(rand_b64)"
  ensure_line "KC_DB_PASSWORD" "${KC_DB_PASSWORD}"
fi

ensure_line "POSTGRES_PASSWORD" "${KC_DB_PASSWORD}"

KEYCLOAK_ADMIN_PASSWORD="$(grep -E '^KEYCLOAK_ADMIN_PASSWORD=' "${ENV_FILE}" | head -n 1 | cut -d= -f2- || true)"
if [[ -z "${KEYCLOAK_ADMIN_PASSWORD}" ]]; then
  KEYCLOAK_ADMIN_PASSWORD="$(rand_b64)"
  ensure_line "KEYCLOAK_ADMIN_PASSWORD" "${KEYCLOAK_ADMIN_PASSWORD}"
fi

KB_OIDC_CLIENT_SECRET="$(grep -E '^KB_OIDC_CLIENT_SECRET=' "${ENV_FILE}" | head -n 1 | cut -d= -f2- || true)"
if [[ -z "${KB_OIDC_CLIENT_SECRET}" ]]; then
  KB_OIDC_CLIENT_SECRET="$(rand_b64)"
  ensure_line "KB_OIDC_CLIENT_SECRET" "${KB_OIDC_CLIENT_SECRET}"
fi

chmod 600 "${ENV_FILE}"
echo "OK: ensured ${ENV_FILE} (mode 600)."
