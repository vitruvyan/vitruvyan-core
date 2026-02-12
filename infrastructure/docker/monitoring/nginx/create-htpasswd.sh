#!/bin/bash
# ============================================================================
# Create htpasswd files for MkDocs authentication
# ============================================================================
# Usage:   ./create-htpasswd.sh
# Output:  .htpasswd (users), .htpasswd_advanced (admins)
# ============================================================================

set -e

HTPASSWD_FILE="/etc/nginx/.htpasswd"
HTPASSWD_ADVANCED_FILE="/etc/nginx/.htpasswd_advanced"

echo "🔐 Creating htpasswd files for MkDocs authentication..."
echo ""

# Install htpasswd if not available
if ! command -v htpasswd &> /dev/null; then
    echo "Installing apache2-utils (htpasswd)..."
    apt-get update && apt-get install -y apache2-utils
fi

# ============================================================================
# BASIC USERS (Full documentation access)
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 BASIC USERS (full documentation access)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Remove old file
rm -f "$HTPASSWD_FILE"

# Create users (interactive)
echo ""
echo "Create basic user 'developer':"
htpasswd -c "$HTPASSWD_FILE" developer

echo ""
echo "Add more users? (y/n)"
read -r ADD_MORE

while [ "$ADD_MORE" = "y" ]; do
    echo "Username:"
    read -r USERNAME
    htpasswd "$HTPASSWD_FILE" "$USERNAME"
    
    echo ""
    echo "Add another? (y/n)"
    read -r ADD_MORE
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

# Remove old file
rm -f "$HTPASSWD_ADVANCED_FILE"

# Create admin users
echo ""
echo "Create advanced user 'admin':"
htpasswd -c "$HTPASSWD_ADVANCED_FILE" admin

echo ""
echo "Add more advanced users? (y/n)"
read -r ADD_MORE_ADV

while [ "$ADD_MORE_ADV" = "y" ]; do
    echo "Username:"
    read -r USERNAME_ADV
    htpasswd "$HTPASSWD_ADVANCED_FILE" "$USERNAME_ADV"
    
    echo ""
    echo "Add another advanced user? (y/n)"
    read -r ADD_MORE_ADV
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
echo "  /public/     → No authentication"
echo "  /            → Basic users ($HTPASSWD_FILE)"
echo "  /planning/   → Advanced users ($HTPASSWD_ADVANCED_FILE)"
echo ""
echo "Next: Restart Nginx to apply changes"
echo "  docker compose restart nginx"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
