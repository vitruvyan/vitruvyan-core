#!/bin/bash
# Portainer Installation Script for Vitruvyan Infrastructure
# Created: February 5, 2026

set -e

echo "🚀 Installing Portainer Community Edition..."
echo ""

# Step 1: Create volume for Portainer data
echo "📦 Creating Portainer data volume..."
sudo docker volume create portainer_data

echo ""
echo "🐳 Starting Portainer container..."

# Step 2: Run Portainer container
sudo docker run -d \
  -p 9000:9000 \
  -p 9443:9443 \
  --name portainer \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest

echo ""
echo "✅ Portainer installation complete!"
echo ""

# Step 3: Show status
echo "📊 Container status:"
sudo docker ps | grep portainer

echo ""
echo "🌐 Access Portainer at:"
echo "   HTTP:  http://$(hostname -I | awk '{print $1}'):9000"
echo "   HTTPS: https://$(hostname -I | awk '{print $1}'):9443"
echo ""
echo "📝 First-time setup:"
echo "   1. Open the URL in your browser"
echo "   2. Create an admin account (username + password)"
echo "   3. Select 'Docker' environment"
echo ""
echo "💡 Optional: Add your user to docker group to avoid sudo:"
echo "   sudo usermod -aG docker \$USER"
echo "   newgrp docker"
echo ""
