#!/bin/bash

# Keycloak Initialization Script
# This script sets up the Vitruvyan realm in Keycloak

set -e

echo "🔐 Keycloak Initialization Script for Vitruvyan"
echo "=============================================="

# Configuration
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
REALM_NAME="vitruvyan"
CLIENT_ID="vitruvyan-web"
API_CLIENT_ID="vitruvyan-api"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to wait for Keycloak to be ready
wait_for_keycloak() {
    echo -e "${YELLOW}⏳ Waiting for Keycloak to be ready...${NC}"
    
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    until curl -sf "${KEYCLOAK_URL}/health/ready" > /dev/null 2>&1; do
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
            echo -e "${RED}❌ Keycloak is not ready after ${MAX_RETRIES} attempts${NC}"
            exit 1
        fi
        echo -e "${YELLOW}   Attempt ${RETRY_COUNT}/${MAX_RETRIES}...${NC}"
        sleep 5
    done
    
    echo -e "${GREEN}✅ Keycloak is ready!${NC}"
}

# Function to get admin token
get_admin_token() {
    echo -e "${YELLOW}🔑 Getting admin token...${NC}"
    
    TOKEN_RESPONSE=$(curl -s -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=${ADMIN_USER}" \
        -d "password=${ADMIN_PASSWORD}" \
        -d "grant_type=password" \
        -d "client_id=admin-cli")
    
    ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    if [ -z "$ACCESS_TOKEN" ]; then
        echo -e "${RED}❌ Failed to get admin token${NC}"
        echo "Response: $TOKEN_RESPONSE"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Admin token obtained${NC}"
}

# Function to check if realm exists
realm_exists() {
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
        "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}")
    
    [ "$RESPONSE" = "200" ]
}

# Function to import realm from JSON
import_realm() {
    echo -e "${YELLOW}📥 Importing Vitruvyan realm...${NC}"
    
    if [ ! -f "keycloak-realm-config.json" ]; then
        echo -e "${RED}❌ keycloak-realm-config.json not found${NC}"
        exit 1
    fi
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
        "${KEYCLOAK_URL}/admin/realms" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json" \
        -d @keycloak-realm-config.json)
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "201" ]; then
        echo -e "${GREEN}✅ Realm imported successfully${NC}"
    else
        echo -e "${RED}❌ Failed to import realm (HTTP ${HTTP_CODE})${NC}"
        echo "Response: $BODY"
        return 1
    fi
}

# Function to create realm manually if import fails
create_realm_manually() {
    echo -e "${YELLOW}📝 Creating realm manually...${NC}"
    
    REALM_JSON='{
        "realm": "'"${REALM_NAME}"'",
        "enabled": true,
        "displayName": "Vitruvyan Platform",
        "registrationAllowed": true,
        "registrationEmailAsUsername": true,
        "rememberMe": true,
        "loginWithEmailAllowed": true,
        "duplicateEmailsAllowed": false,
        "resetPasswordAllowed": true,
        "editUsernameAllowed": false,
        "sslRequired": "external",
        "bruteForceProtected": true
    }'
    
    curl -s -X POST "${KEYCLOAK_URL}/admin/realms" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$REALM_JSON"
    
    echo -e "${GREEN}✅ Realm created${NC}"
}

# Function to generate client secret
generate_client_secret() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Function to create web client
create_web_client() {
    echo -e "${YELLOW}🌐 Creating web client...${NC}"
    
    CLIENT_JSON='{
        "clientId": "'"${CLIENT_ID}"'",
        "name": "Vitruvyan Web Application",
        "enabled": true,
        "publicClient": true,
        "protocol": "openid-connect",
        "standardFlowEnabled": true,
        "implicitFlowEnabled": false,
        "directAccessGrantsEnabled": true,
        "redirectUris": [
            "https://vitruvyan.com/*",
            "https://*.vitruvyan.com/*",
            "http://localhost:3000/*",
            "http://localhost:5173/*"
        ],
        "webOrigins": [
            "https://vitruvyan.com",
            "https://*.vitruvyan.com",
            "http://localhost:3000",
            "http://localhost:5173"
        ],
        "attributes": {
            "pkce.code.challenge.method": "S256",
            "post.logout.redirect.uris": "+"
        }
    }'
    
    curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/clients" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$CLIENT_JSON"
    
    echo -e "${GREEN}✅ Web client created${NC}"
}

# Function to create API client
create_api_client() {
    echo -e "${YELLOW}🔧 Creating API client...${NC}"
    
    API_CLIENT_SECRET=$(generate_client_secret)
    
    CLIENT_JSON='{
        "clientId": "'"${API_CLIENT_ID}"'",
        "name": "Vitruvyan API Backend",
        "enabled": true,
        "publicClient": false,
        "protocol": "openid-connect",
        "serviceAccountsEnabled": true,
        "authorizationServicesEnabled": true,
        "secret": "'"${API_CLIENT_SECRET}"'"
    }'
    
    curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/clients" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$CLIENT_JSON"
    
    echo -e "${GREEN}✅ API client created${NC}"
    echo -e "${YELLOW}⚠️  API Client Secret: ${API_CLIENT_SECRET}${NC}"
    echo -e "${YELLOW}⚠️  Save this secret securely!${NC}"
    
    # Save to file
    echo "API_CLIENT_SECRET=${API_CLIENT_SECRET}" > .api-client-secret
    echo -e "${GREEN}✅ Secret saved to .api-client-secret${NC}"
}

# Function to create roles
create_roles() {
    echo -e "${YELLOW}👥 Creating realm roles...${NC}"
    
    ROLES=("user" "premium" "admin")
    
    for ROLE in "${ROLES[@]}"; do
        ROLE_JSON='{"name": "'"${ROLE}"'"}'
        
        curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/roles" \
            -H "Authorization: Bearer ${ACCESS_TOKEN}" \
            -H "Content-Type: application/json" \
            -d "$ROLE_JSON"
        
        echo -e "${GREEN}   ✅ Role '${ROLE}' created${NC}"
    done
}

# Function to set default roles
set_default_roles() {
    echo -e "${YELLOW}⚙️  Setting default roles...${NC}"
    
    # Get role ID
    ROLE_ID=$(curl -s "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/roles/user" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    
    if [ -n "$ROLE_ID" ]; then
        curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/roles/default" \
            -H "Authorization: Bearer ${ACCESS_TOKEN}" \
            -H "Content-Type: application/json" \
            -d '[{"id":"'"${ROLE_ID}"'","name":"user"}]'
        
        echo -e "${GREEN}✅ Default role set${NC}"
    fi
}

# Main execution
main() {
    echo ""
    echo "Configuration:"
    echo "  Keycloak URL: ${KEYCLOAK_URL}"
    echo "  Realm: ${REALM_NAME}"
    echo "  Client ID: ${CLIENT_ID}"
    echo ""
    
    # Wait for Keycloak
    wait_for_keycloak
    
    # Get admin token
    get_admin_token
    
    # Check if realm exists
    if realm_exists; then
        echo -e "${YELLOW}⚠️  Realm '${REALM_NAME}' already exists${NC}"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}🗑️  Deleting existing realm...${NC}"
            curl -s -X DELETE "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}" \
                -H "Authorization: Bearer ${ACCESS_TOKEN}"
            echo -e "${GREEN}✅ Realm deleted${NC}"
        else
            echo -e "${YELLOW}⏭️  Skipping realm creation${NC}"
            exit 0
        fi
    fi
    
    # Try to import realm from JSON
    if import_realm; then
        echo -e "${GREEN}✅ Realm configuration imported from JSON${NC}"
    else
        echo -e "${YELLOW}⚠️  JSON import failed, creating realm manually...${NC}"
        create_realm_manually
        create_web_client
        create_api_client
        create_roles
        set_default_roles
    fi
    
    echo ""
    echo -e "${GREEN}✅ Keycloak initialization complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Access Keycloak admin console: ${KEYCLOAK_URL}/admin"
    echo "2. Login with admin credentials"
    echo "3. Review the '${REALM_NAME}' realm configuration"
    echo "4. Configure DNS: auth.vitruvyan.com -> your server"
    echo "5. Setup nginx reverse proxy with SSL"
    echo "6. Update frontend .env with production URLs"
    echo ""
}

# Run main function
main
