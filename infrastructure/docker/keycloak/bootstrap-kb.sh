#!/usr/bin/env bash
set -euo pipefail

REALM="${REALM:-vitruvyan}"
CLIENT_ID="${CLIENT_ID:-kb}"
BASE_URL="${BASE_URL:-https://kb.vitruvyan.com}"
KC_HTTP_BASE="${KC_HTTP_BASE:-http://localhost:8080/auth}"

KEYCLOAK_ADMIN="${KEYCLOAK_ADMIN:-admin}"
KEYCLOAK_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-}"
KB_OIDC_CLIENT_SECRET="${KB_OIDC_CLIENT_SECRET:-}"

if [[ -z "${KEYCLOAK_ADMIN_PASSWORD}" ]]; then
  echo "ERROR: KEYCLOAK_ADMIN_PASSWORD is required."
  exit 1
fi

if [[ -z "${KB_OIDC_CLIENT_SECRET}" ]]; then
  echo "ERROR: KB_OIDC_CLIENT_SECRET is required."
  exit 1
fi

KC_BIN="/opt/keycloak/bin"
KCADM="${KC_BIN}/kcadm.sh"

wait_ready() {
  for _ in $(seq 1 60); do
    if ${KCADM} config credentials \
      --server "${KC_HTTP_BASE}" \
      --realm master \
      --user "${KEYCLOAK_ADMIN}" \
      --password "${KEYCLOAK_ADMIN_PASSWORD}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "ERROR: Keycloak not ready at ${KC_HTTP_BASE}."
  return 1
}

wait_ready

ensure_realm() {
  if ${KCADM} get "realms/${REALM}" >/dev/null 2>&1; then
    return 0
  fi
  ${KCADM} create realms -s "realm=${REALM}" -s enabled=true >/dev/null
}

ensure_group() {
  local group_path="$1"
  if ${KCADM} get "groups?search=$(basename "${group_path}")" -r "${REALM}" | grep -q "\"path\" *: *\"${group_path}\""; then
    return 0
  fi
  ${KCADM} create groups -r "${REALM}" -s "name=$(basename "${group_path}")" >/dev/null
}

ensure_client() {
  local existing
  existing="$(${KCADM} get clients -r "${REALM}" -q "clientId=${CLIENT_ID}" | grep -oE '"id" *: *"[^"]+"' | head -n 1 | cut -d'"' -f4 || true)"
  if [[ -n "${existing}" ]]; then
    echo "${existing}"
    return 0
  fi

local client_id
client_id="$(${KCADM} create clients -r "${REALM}" \
    -s "clientId=${CLIENT_ID}" \
    -s enabled=true \
    -s protocol=openid-connect \
    -s publicClient=false \
    -s "secret=${KB_OIDC_CLIENT_SECRET}" \
    -s standardFlowEnabled=true \
    -s directAccessGrantsEnabled=false \
    -s serviceAccountsEnabled=false \
    -s "baseUrl=${BASE_URL}/" \
    -s "rootUrl=${BASE_URL}" \
    -s "redirectUris=[\"${BASE_URL}/oauth2/callback\",\"${BASE_URL}/oauth2-advanced/callback\"]" \
    -s "webOrigins=[\"${BASE_URL}\"]" \
    -i | tr -d '\r')"

if [[ -z "${client_id}" ]]; then
  echo "ERROR: failed to create client ${CLIENT_ID}."
  exit 1
fi

echo "${client_id}"
}

ensure_groups_mapper() {
  local client_uuid="$1"
  if [[ -z "${client_uuid}" ]]; then
    echo "ERROR: empty client UUID for protocol mapper."
    exit 1
  fi
  # Add "groups" claim into ID token and access token.
  # Skip if already present.
  if ${KCADM} get "clients/${client_uuid}/protocol-mappers/models" -r "${REALM}" | grep -q "\"name\" *: *\"groups\""; then
    return 0
  fi

  ${KCADM} create "clients/${client_uuid}/protocol-mappers/models" -r "${REALM}" \
    -s "name=groups" \
    -s "protocol=openid-connect" \
    -s "protocolMapper=oidc-group-membership-mapper" \
    -s "consentRequired=false" \
    -s "config.\"full.path\"=true" \
    -s "config.\"id.token.claim\"=true" \
    -s "config.\"access.token.claim\"=true" \
    -s "config.\"userinfo.token.claim\"=true" \
    -s "config.\"claim.name\"=groups" >/dev/null
}

ensure_realm
ensure_group "/kb-developers"
ensure_group "/kb-admins"

CLIENT_UUID="$(ensure_client)"
ensure_groups_mapper "${CLIENT_UUID}"

echo "OK: Keycloak KB realm/client bootstrap complete."
