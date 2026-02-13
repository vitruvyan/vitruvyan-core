#!/bin/bash
# ============================================================================
# Create htpasswd files for MkDocs authentication
# ============================================================================
# Usage:   ./create-htpasswd.sh
# Output:  .htpasswd (users), .htpasswd_advanced (admins)
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTPASSWD_FILE="${SCRIPT_DIR}/.htpasswd"
HTPASSWD_ADVANCED_FILE="${SCRIPT_DIR}/.htpasswd_advanced"

echo "🔐 Creating htpasswd files for MkDocs authentication..."
echo ""

if ! command -v openssl &> /dev/null; then
  echo "ERROR: openssl not found. Install OpenSSL and retry."
  exit 1
fi

hash_password() {
  # Apache MD5 (APR1) hash compatible with Nginx auth_basic
  # Use -stdin so we can safely pipe the password in (non-interactive).
  openssl passwd -apr1 -stdin
}

add_user() {
  local file="$1"
  local username="$2"
  local password="$3"
  local hashed
  hashed="$(printf '%s' "$password" | hash_password)"
  printf '%s:%s\n' "$username" "$hashed" >> "$file"
}

# ============================================================================
# BASIC USERS (Full documentation access)
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 BASIC USERS (full documentation access)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

rm -f "$HTPASSWD_FILE" && touch "$HTPASSWD_FILE"
# Must be readable by the nginx worker inside the container (bind mount keeps host perms)
chmod 644 "$HTPASSWD_FILE"

echo ""
echo "Create basic user 'developer' (password hidden):"
read -r -s -p "Password: " DEV_PW
echo ""
read -r -s -p "Confirm:  " DEV_PW_2
echo ""
if [ "$DEV_PW" != "$DEV_PW_2" ]; then
  echo "ERROR: passwords do not match."
  exit 1
fi
add_user "$HTPASSWD_FILE" "developer" "$DEV_PW"
unset DEV_PW DEV_PW_2

while true; do
  echo ""
  read -r -p "Add more basic users? (y/n) " ADD_MORE
  if [ "$ADD_MORE" != "y" ]; then
    break
  fi
  read -r -p "Username: " USERNAME
  read -r -s -p "Password: " USER_PW
  echo ""
  read -r -s -p "Confirm:  " USER_PW_2
  echo ""
  if [ "$USER_PW" != "$USER_PW_2" ]; then
    echo "ERROR: passwords do not match."
    exit 1
  fi
  add_user "$HTPASSWD_FILE" "$USERNAME" "$USER_PW"
  unset USERNAME USER_PW USER_PW_2
done

echo ""
echo "✅ Basic users file created: $HTPASSWD_FILE"
echo ""

# ============================================================================
# ADVANCED USERS (Planning, architecture, technical debt)
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 ADVANCED USERS (planning, technical docs)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

rm -f "$HTPASSWD_ADVANCED_FILE" && touch "$HTPASSWD_ADVANCED_FILE"
# Must be readable by the nginx worker inside the container (bind mount keeps host perms)
chmod 644 "$HTPASSWD_ADVANCED_FILE"

echo ""
echo "Create advanced user 'admin' (password hidden):"
read -r -s -p "Password: " ADMIN_PW
echo ""
read -r -s -p "Confirm:  " ADMIN_PW_2
echo ""
if [ "$ADMIN_PW" != "$ADMIN_PW_2" ]; then
  echo "ERROR: passwords do not match."
  exit 1
fi
add_user "$HTPASSWD_ADVANCED_FILE" "admin" "$ADMIN_PW"
unset ADMIN_PW ADMIN_PW_2

while true; do
  echo ""
  read -r -p "Add more advanced users? (y/n) " ADD_MORE_ADV
  if [ "$ADD_MORE_ADV" != "y" ]; then
    break
  fi
  read -r -p "Username: " USERNAME_ADV
  read -r -s -p "Password: " USER_ADV_PW
  echo ""
  read -r -s -p "Confirm:  " USER_ADV_PW_2
  echo ""
  if [ "$USER_ADV_PW" != "$USER_ADV_PW_2" ]; then
    echo "ERROR: passwords do not match."
    exit 1
  fi
  add_user "$HTPASSWD_ADVANCED_FILE" "$USERNAME_ADV" "$USER_ADV_PW"
  unset USERNAME_ADV USER_ADV_PW USER_ADV_PW_2
done

echo ""
echo "✅ Advanced users file created: $HTPASSWD_ADVANCED_FILE"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ HTPASSWD SETUP COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Basic users:    $(wc -l < "$HTPASSWD_FILE") users"
echo "Advanced users: $(wc -l < "$HTPASSWD_ADVANCED_FILE") users"
echo ""
echo "Access levels:"
echo "  /, /it/                 → No authentication (public landing)"
echo "  /(it/)?docs/...         → Basic users ($HTPASSWD_FILE)"
echo "  /(it/)?docs/planning/... → Advanced users ($HTPASSWD_ADVANCED_FILE)"
echo ""
echo "Next: Restart Nginx to apply changes"
echo "  docker compose restart nginx"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
