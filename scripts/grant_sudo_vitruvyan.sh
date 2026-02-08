#!/bin/bash
# Grant sudo privileges to vitruvyan user
# This script must be run as root
# Created: February 5, 2026

set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run as root"
    echo "   Run: su -"
    echo "   Then: bash /home/vitruvyan/vitruvyan-core/scripts/grant_sudo_vitruvyan.sh"
    exit 1
fi

echo "🔐 Granting sudo privileges to user 'vitruvyan'..."
echo ""

# Add user to sudo group
usermod -aG sudo vitruvyan

echo "✅ User 'vitruvyan' added to sudo group"
echo ""

# Also add to docker group for Docker commands without sudo
if getent group docker > /dev/null 2>&1; then
    usermod -aG docker vitruvyan
    echo "✅ User 'vitruvyan' added to docker group"
else
    echo "⚠️  Docker group not found (skipping)"
fi

echo ""
echo "📝 Changes applied:"
groups vitruvyan

echo ""
echo "🔄 User 'vitruvyan' needs to log out and log back in for changes to take effect"
echo "   Or run: su - vitruvyan"
echo ""
echo "✅ Done!"
