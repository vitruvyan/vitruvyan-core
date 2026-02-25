#!/bin/bash

# Complete Keycloak Setup and Deployment Script
# This script deploys Keycloak with PostgreSQL and configures everything

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╦  ╦┬┌┬┐┬─┐┬ ┬┬  ┬┬ ┬┌─┐┌┐┌  ╦╔═╔═╗╦ ╦╔═╗╦  ╔═╗╔═╗╦╔═
╚╗╔╝│ │ ├┬┘│ │└┐┌┘└┬┘├─┤│││  ╠╩╗║╣ ╚╦╝║  ║  ║ ║╠═╣╠╩╗
 ╚╝ ┴ ┴ ┴└─└─┘ └┘  ┴ ┴ ┴┘└┘  ╩ ╩╚═╝ ╩ ╚═╝╩═╝╚═╝╩ ╩╩ ╩
EOF
echo -e "${NC}"
echo -e "${YELLOW}Complete Setup & Deployment${NC}"
echo ""

# Check if .env.keycloak exists
if [ ! -f ".env.keycloak" ]; then
    echo -e "${RED}❌ .env.keycloak not found!${NC}"
    echo "Creating template..."
    cat > .env.keycloak << 'EOL'
# Keycloak Database Configuration
KEYCLOAK_DB_PASSWORD=your_secure_db_password_here

# Keycloak Admin Configuration
KEYCLOAK_ADMIN_PASSWORD=your_secure_admin_password_here

# Keycloak Hostname Configuration
KEYCLOAK_HOSTNAME=auth.vitruvyan.com
KC_HOSTNAME_STRICT_HTTPS=true

# Ports
KEYCLOAK_PORT=8080
KEYCLOAK_HTTPS_PORT=8443
EOL
    echo -e "${YELLOW}⚠️  Please edit .env.keycloak with your passwords and configuration${NC}"
    exit 1
fi

# Source environment
source .env.keycloak

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
    
    local missing=()
    
    command -v docker >/dev/null 2>&1 || missing+=("docker")
    command -v docker-compose >/dev/null 2>&1 || missing+=("docker-compose")
    command -v curl >/dev/null 2>&1 || missing+=("curl")
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing required tools: ${missing[*]}${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All prerequisites met${NC}"
}

# Function to create network if it doesn't exist
create_network() {
    echo -e "${YELLOW}🌐 Setting up Docker network...${NC}"
    
    if ! docker network inspect vitruvyan-network >/dev/null 2>&1; then
        docker network create vitruvyan-network
        echo -e "${GREEN}✅ Network created${NC}"
    else
        echo -e "${GREEN}✅ Network already exists${NC}"
    fi
}

# Function to start Keycloak stack
start_keycloak() {
    echo -e "${YELLOW}🚀 Starting Keycloak stack...${NC}"
    
    docker-compose -f docker-compose.keycloak.yml --env-file .env.keycloak up -d
    
    echo -e "${GREEN}✅ Keycloak stack started${NC}"
}

# Function to wait for services
wait_for_services() {
    echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
    
    MAX_WAIT=120
    ELAPSED=0
    
    while [ $ELAPSED -lt $MAX_WAIT ]; do
        if docker-compose -f docker-compose.keycloak.yml ps | grep -q "healthy"; then
            echo -e "${GREEN}✅ Services are healthy${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}   Waiting... (${ELAPSED}s/${MAX_WAIT}s)${NC}"
        sleep 5
        ELAPSED=$((ELAPSED + 5))
    done
    
    echo -e "${RED}❌ Services did not become healthy in time${NC}"
    docker-compose -f docker-compose.keycloak.yml logs --tail=50
    exit 1
}

# Function to initialize Keycloak
initialize_keycloak() {
    echo -e "${YELLOW}🔧 Initializing Keycloak configuration...${NC}"
    
    if [ -f "setup-keycloak.sh" ]; then
        chmod +x setup-keycloak.sh
        
        # Set environment variables for the script
        export KEYCLOAK_URL="http://localhost:${KEYCLOAK_PORT}"
        export KEYCLOAK_ADMIN=admin
        export KEYCLOAK_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD}"
        
        ./setup-keycloak.sh
    else
        echo -e "${RED}❌ setup-keycloak.sh not found${NC}"
        exit 1
    fi
}

# Function to setup SSL with Let's Encrypt
setup_ssl() {
    echo -e "${YELLOW}🔐 SSL Certificate Setup${NC}"
    echo ""
    echo "To enable HTTPS with Let's Encrypt:"
    echo ""
    echo "1. Ensure DNS is configured:"
    echo "   auth.vitruvyan.com -> Your Server IP"
    echo ""
    echo "2. Install certbot:"
    echo "   sudo apt-get update"
    echo "   sudo apt-get install certbot python3-certbot-nginx"
    echo ""
    echo "3. Stop nginx temporarily:"
    echo "   sudo systemctl stop nginx"
    echo ""
    echo "4. Generate certificate:"
    echo "   sudo certbot certonly --standalone -d auth.vitruvyan.com"
    echo ""
    echo "5. Copy nginx configuration:"
    echo "   sudo cp nginx-keycloak.conf /etc/nginx/sites-available/auth.vitruvyan.com"
    echo "   sudo ln -s /etc/nginx/sites-available/auth.vitruvyan.com /etc/nginx/sites-enabled/"
    echo ""
    echo "6. Test and restart nginx:"
    echo "   sudo nginx -t"
    echo "   sudo systemctl start nginx"
    echo ""
    echo "7. Setup auto-renewal:"
    echo "   sudo certbot renew --dry-run"
    echo ""
    
    read -p "Press Enter to continue..."
}

# Function to display status
show_status() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   Keycloak Deployment Complete! ✅    ║${NC}"
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo ""
    echo -e "${YELLOW}Service URLs:${NC}"
    echo "  Local:  http://localhost:${KEYCLOAK_PORT}"
    echo "  Public: https://${KEYCLOAK_HOSTNAME} (after SSL setup)"
    echo ""
    echo -e "${YELLOW}Admin Console:${NC}"
    echo "  URL:      http://localhost:${KEYCLOAK_PORT}/admin"
    echo "  Username: admin"
    echo "  Password: ${KEYCLOAK_ADMIN_PASSWORD}"
    echo ""
    echo -e "${YELLOW}Realm Configuration:${NC}"
    echo "  Realm:     vitruvyan"
    echo "  Client ID: vitruvyan-web"
    echo ""
    echo -e "${YELLOW}Container Status:${NC}"
    docker-compose -f docker-compose.keycloak.yml ps
    echo ""
    echo -e "${YELLOW}Logs:${NC}"
    echo "  View logs: docker-compose -f docker-compose.keycloak.yml logs -f"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Configure DNS: auth.vitruvyan.com"
    echo "  2. Setup SSL certificates (see setup_ssl function)"
    echo "  3. Configure nginx reverse proxy"
    echo "  4. Update frontend .env with production URLs"
    echo "  5. Test authentication flow"
    echo ""
}

# Function to show manual steps
show_manual_steps() {
    cat > KEYCLOAK_SETUP_GUIDE.md << 'EOF'
# Keycloak Setup Guide for Vitruvyan

## Quick Start

\`\`\`bash
# 1. Edit .env.keycloak with your passwords
nano .env.keycloak

# 2. Run deployment script
chmod +x deploy-keycloak.sh
./deploy-keycloak.sh
\`\`\`

## Manual Setup Steps

### 1. DNS Configuration

Add an A record for your domain:
\`\`\`
auth.vitruvyan.com -> YOUR_SERVER_IP
\`\`\`

Verify DNS propagation:
\`\`\`bash
dig auth.vitruvyan.com
nslookup auth.vitruvyan.com
\`\`\`

### 2. SSL Certificate (Let's Encrypt)

\`\`\`bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d auth.vitruvyan.com --non-interactive --agree-tos --email your@email.com

# Certificates will be saved to:
# /etc/letsencrypt/live/auth.vitruvyan.com/
\`\`\`

### 3. Nginx Configuration

\`\`\`bash
# Copy configuration
sudo cp nginx-keycloak.conf /etc/nginx/sites-available/auth.vitruvyan.com

# Enable site
sudo ln -s /etc/nginx/sites-available/auth.vitruvyan.com /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
\`\`\`

### 4. Configure Frontend

Update your frontend `.env`:

\`\`\`bash
# Production
NEXT_PUBLIC_KEYCLOAK_URL=https://auth.vitruvyan.com
NEXT_PUBLIC_KEYCLOAK_REALM=vitruvyan
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=vitruvyan-web

# For Vite/React
VITE_KEYCLOAK_URL=https://auth.vitruvyan.com
VITE_KEYCLOAK_REALM=vitruvyan
VITE_KEYCLOAK_CLIENT_ID=vitruvyan-web
\`\`\`

### 5. Test Authentication

1. Access Keycloak admin: `https://auth.vitruvyan.com/admin`
2. Login with admin credentials
3. Go to Clients -> vitruvyan-web
4. Verify redirect URIs include all your subdomains
5. Test login from your application

## Docker Commands

\`\`\`bash
# View logs
docker-compose -f docker-compose.keycloak.yml logs -f

# Restart services
docker-compose -f docker-compose.keycloak.yml restart

# Stop services
docker-compose -f docker-compose.keycloak.yml down

# Full cleanup (WARNING: deletes data)
docker-compose -f docker-compose.keycloak.yml down -v
\`\`\`

## Keycloak Admin Tasks

### Create a Test User

1. Login to admin console
2. Go to Users -> Add user
3. Fill in details, click Save
4. Go to Credentials tab
5. Set password (uncheck "Temporary")
6. Go to Role Mappings tab
7. Assign "user" role (or "premium" for testing premium features)

### Configure Client for All Subdomains

In Keycloak admin console:

1. Clients -> vitruvyan-web -> Settings
2. Valid redirect URIs:
   - `https://vitruvyan.com/*`
   - `https://*.vitruvyan.com/*`
3. Valid post logout redirect URIs: `+` (means same as redirect URIs)
4. Web origins:
   - `https://vitruvyan.com`
   - `https://*.vitruvyan.com`

### Backup Configuration

\`\`\`bash
# Export realm
docker exec -it vitruvyan-keycloak /opt/keycloak/bin/kc.sh export \
  --dir /tmp/export --realm vitruvyan

# Copy from container
docker cp vitruvyan-keycloak:/tmp/export ./keycloak-backup/
\`\`\`

## Troubleshooting

### Cannot connect to Keycloak

\`\`\`bash
# Check if services are running
docker-compose -f docker-compose.keycloak.yml ps

# Check logs
docker-compose -f docker-compose.keycloak.yml logs keycloak
docker-compose -f docker-compose.keycloak.yml logs postgres-keycloak

# Verify network
docker network inspect vitruvyan-network
\`\`\`

### SSL Issues

\`\`\`bash
# Verify certificate
sudo certbot certificates

# Renew certificate manually
sudo certbot renew --force-renewal

# Check nginx error log
sudo tail -f /var/log/nginx/keycloak_error.log
\`\`\`

### CORS Errors

In Keycloak admin:
1. Clients -> vitruvyan-web -> Settings
2. Ensure Web Origins includes your domain
3. Add `+` to automatically allow all redirect URIs

### Token Issues

Check token lifetime in Keycloak:
1. Realm Settings -> Tokens
2. Adjust token lifespans as needed
3. Default: Access Token = 5 minutes

## Security Recommendations

1. **Change default passwords** in `.env.keycloak`
2. **Enable HTTPS only** in production (KC_HOSTNAME_STRICT_HTTPS=true)
3. **Configure rate limiting** in nginx
4. **Enable 2FA** for admin account
5. **Regular backups** of PostgreSQL database
6. **Monitor logs** for suspicious activity
7. **Keep Keycloak updated** to latest stable version

## Integration with Frontend

The `utils/keycloak.js` file handles:
- Auto-detection of production vs development
- Token refresh before expiration
- Role-based access (user, premium, admin)
- Cross-subdomain authentication

Example usage:

\`\`\`javascript
import { initKeycloak, login, logout, isPremiumUser } from '@/utils/keycloak';

// Initialize on app load
useEffect(() => {
  initKeycloak(
    (kc) => console.log('Auth success'),
    (err) => console.error('Auth error', err)
  );
}, []);

// Login button
<button onClick={login}>Login</button>

// Check premium status
if (isPremiumUser()) {
  // Show premium features
}
\`\`\`

## Production Checklist

- [ ] DNS configured for auth.vitruvyan.com
- [ ] SSL certificate installed and valid
- [ ] Nginx reverse proxy configured
- [ ] Keycloak realm imported
- [ ] Test user created
- [ ] Client redirect URIs configured for all subdomains
- [ ] Frontend .env updated with production URLs
- [ ] Token refresh working
- [ ] Cross-subdomain SSO tested
- [ ] Backup strategy in place
- [ ] Monitoring configured

EOF

    echo -e "${GREEN}✅ Setup guide created: KEYCLOAK_SETUP_GUIDE.md${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}Starting Keycloak deployment...${NC}"
    echo ""
    
    check_prerequisites
    create_network
    start_keycloak
    wait_for_services
    
    echo ""
    read -p "Initialize Keycloak realm now? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        initialize_keycloak
    fi
    
    show_status
    show_manual_steps
    
    echo ""
    read -p "Show SSL setup instructions? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_ssl
    fi
    
    echo ""
    echo -e "${GREEN}🎉 Deployment complete!${NC}"
    echo -e "${YELLOW}📖 Read KEYCLOAK_SETUP_GUIDE.md for detailed instructions${NC}"
}

# Run main
main
