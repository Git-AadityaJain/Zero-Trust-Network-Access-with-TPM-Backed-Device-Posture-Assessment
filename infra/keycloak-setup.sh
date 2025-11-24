#!/bin/bash
# Keycloak setup script
# This script helps configure Keycloak clients after initial startup

echo "Waiting for Keycloak to be ready..."
sleep 30

KEYCLOAK_URL="http://localhost:8080"
REALM="master"
ADMIN_USER="admin"
ADMIN_PASSWORD="adminsecure123"

# Get admin token
TOKEN=$(curl -s -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${ADMIN_USER}" \
  -d "password=${ADMIN_PASSWORD}" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
  echo "Failed to get admin token. Make sure Keycloak is running."
  exit 1
fi

echo "Keycloak is ready!"
echo "Admin Console: ${KEYCLOAK_URL}"
echo "Realm: ${REALM}"
echo ""
echo "You can now configure clients manually or use the Keycloak Admin Console."

