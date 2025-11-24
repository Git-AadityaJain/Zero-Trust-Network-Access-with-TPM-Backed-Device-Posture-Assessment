#!/bin/bash

# External Access Setup Script
# This script helps configure the ZTNA platform for external access

set -e

echo "=========================================="
echo "ZTNA External Access Setup"
echo "=========================================="
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "⚠️  ngrok is not installed."
    echo "Please install ngrok from https://ngrok.com/download"
    echo ""
    read -p "Do you want to continue with manual setup? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get external URLs
echo "Enter your external access URLs:"
echo ""
read -p "Frontend/Backend URL (e.g., https://abc123.ngrok.io): " FRONTEND_URL
read -p "Keycloak URL (e.g., https://def456.ngrok.io): " KEYCLOAK_URL

# Validate URLs
if [[ ! $FRONTEND_URL =~ ^https?:// ]]; then
    echo "❌ Invalid frontend URL format"
    exit 1
fi

if [[ ! $KEYCLOAK_URL =~ ^https?:// ]]; then
    echo "❌ Invalid Keycloak URL format"
    exit 1
fi

echo ""
echo "Updating configuration files..."

# Update docker-compose.yml
if [ -f "infra/docker-compose.yml" ]; then
    echo "📝 Updating docker-compose.yml..."
    # This is a template - user should manually update
    echo "   Please update infra/docker-compose.yml with:"
    echo "   - REACT_APP_API_URL=${FRONTEND_URL}/api"
    echo "   - REACT_APP_KEYCLOAK_URL=${KEYCLOAK_URL}"
    echo "   - CORS_ORIGIN=${FRONTEND_URL},http://localhost:3000"
fi

# Create/update frontend .env
if [ -f "frontend/.env" ]; then
    echo "📝 Updating frontend/.env..."
    cat >> frontend/.env << EOF

# External Access Configuration
REACT_APP_API_URL=${FRONTEND_URL}/api
REACT_APP_KEYCLOAK_URL=${KEYCLOAK_URL}
EOF
else
    echo "📝 Creating frontend/.env..."
    cat > frontend/.env << EOF
REACT_APP_API_URL=${FRONTEND_URL}/api
REACT_APP_KEYCLOAK_URL=${KEYCLOAK_URL}
REACT_APP_KEYCLOAK_REALM=master
REACT_APP_KEYCLOAK_CLIENT_ID=admin-frontend
EOF
fi

# Update backend .env
if [ -f "backend/.env" ]; then
    echo "📝 Updating backend/.env..."
    # Add CORS_ORIGIN if not present
    if ! grep -q "CORS_ORIGIN" backend/.env; then
        echo "CORS_ORIGIN=${FRONTEND_URL},http://localhost:3000" >> backend/.env
    fi
    
    # Update OIDC_ISSUER if present
    if grep -q "OIDC_ISSUER" backend/.env; then
        sed -i.bak "s|OIDC_ISSUER=.*|OIDC_ISSUER=${KEYCLOAK_URL}/realms/master|" backend/.env
        sed -i.bak "s|OIDC_JWKS_URI=.*|OIDC_JWKS_URI=${KEYCLOAK_URL}/realms/master/protocol/openid-connect/certs|" backend/.env
    fi
else
    echo "⚠️  backend/.env not found. Please create it manually."
fi

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Update Keycloak client configuration:"
echo "   - Access: ${KEYCLOAK_URL}"
echo "   - Add to Valid Redirect URIs: ${FRONTEND_URL}/callback"
echo "   - Add to Web Origins: ${FRONTEND_URL}"
echo "   - Add to Post Logout Redirect URIs: ${FRONTEND_URL}/login"
echo ""
echo "2. Update DPA configuration:"
echo "   - Set backend URL to: ${FRONTEND_URL}/api"
echo ""
echo "3. Restart services:"
echo "   cd infra && docker-compose restart frontend backend"
echo ""
echo "4. Test external access:"
echo "   - Web: ${FRONTEND_URL}"
echo "   - Keycloak: ${KEYCLOAK_URL}"
echo ""
echo "✅ Configuration files updated!"
echo ""

