#!/usr/bin/env python3
"""
Script to verify Keycloak configuration
Checks if clients exist and are properly configured
"""

import requests
import json
import sys

KEYCLOAK_URL = "http://localhost:8080"
REALM = "master"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "adminsecure123"

def get_admin_token():
    """Get admin token from Keycloak"""
    try:
        response = requests.post(
            f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
            data={
                "username": ADMIN_USER,
                "password": ADMIN_PASSWORD,
                "grant_type": "password",
                "client_id": "admin-cli"
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"❌ Failed to get admin token: {e}")
        return None

def get_clients(token):
    """Get all clients from the realm"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Failed to get clients: {e}")
        return []

def check_client(client_id, clients):
    """Check if a client exists and is properly configured"""
    client = next((c for c in clients if c.get("clientId") == client_id), None)
    
    if not client:
        print(f"❌ Client '{client_id}' not found")
        return False
    
    print(f"✅ Client '{client_id}' exists")
    
    # Check configuration
    issues = []
    
    if client.get("enabled") != True:
        issues.append("Client is not enabled")
    
    if client_id == "admin-frontend":
        if client.get("publicClient") != True:
            issues.append("Should be a public client")
        if client.get("standardFlowEnabled") != True:
            issues.append("Standard flow should be enabled")
        redirect_uris = client.get("redirectUris", [])
        if "http://localhost:3000/callback" not in redirect_uris and "http://localhost/callback" not in redirect_uris:
            issues.append("Missing required redirect URIs")
    
    if client_id == "ZTNA-Platform-realm":
        if client.get("bearerOnly") != True:
            issues.append("Should be bearer-only")
    
    if issues:
        print(f"  ⚠️  Issues: {', '.join(issues)}")
        return False
    else:
        print(f"  ✅ Configuration looks good")
        return True

def get_client_mappers(token, client_id):
    """Get protocol mappers for a client"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        # First get client ID
        clients = get_clients(token)
        client = next((c for c in clients if c.get("clientId") == client_id), None)
        if not client:
            return []
        
        client_uuid = client["id"]
        response = requests.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_uuid}/protocol-mappers/models",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Failed to get mappers for {client_id}: {e}")
        return []

def check_audience_mapper(token, client_id):
    """Check if audience mapper exists for client"""
    mappers = get_client_mappers(token, client_id)
    audience_mappers = [m for m in mappers if m.get("protocolMapper") == "oidc-audience-mapper"]
    
    if not audience_mappers:
        print(f"  ⚠️  No audience mapper found for '{client_id}'")
        return False
    
    print(f"  ✅ Audience mapper exists for '{client_id}'")
    for mapper in audience_mappers:
        config = mapper.get("config", {})
        included_audience = config.get("included.client.audience")
        if included_audience == client_id:
            print(f"  ✅ Audience mapper configured correctly (audience: {included_audience})")
            return True
        else:
            print(f"  ⚠️  Audience mapper has wrong audience: {included_audience}, expected: {client_id}")
            return False

def get_realm_info(token):
    """Get realm information"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Failed to get realm info: {e}")
        return None

def main():
    print("🔍 Verifying Keycloak Configuration...")
    print(f"Keycloak URL: {KEYCLOAK_URL}")
    print(f"Realm: {REALM}\n")
    
    # Check if Keycloak is accessible
    try:
        response = requests.get(f"{KEYCLOAK_URL}/health/ready", timeout=5)
        if response.status_code == 200:
            print("✅ Keycloak is accessible\n")
        else:
            print(f"⚠️  Keycloak health check returned: {response.status_code}\n")
    except Exception as e:
        print(f"❌ Cannot connect to Keycloak: {e}")
        print("Make sure Keycloak is running and accessible at http://localhost:8080")
        sys.exit(1)
    
    # Get admin token
    token = get_admin_token()
    if not token:
        sys.exit(1)
    
    print("✅ Admin token obtained\n")
    
    # Get realm info
    realm_info = get_realm_info(token)
    if realm_info:
        print(f"✅ Realm '{REALM}' exists")
        print(f"   Display Name: {realm_info.get('displayName', 'N/A')}")
        print(f"   Enabled: {realm_info.get('enabled', False)}\n")
    
    # Get clients
    clients = get_clients(token)
    print(f"✅ Found {len(clients)} clients\n")
    
    # Check required clients
    print("Checking required clients...\n")
    
    admin_frontend_ok = check_client("admin-frontend", clients)
    print()
    
    ztna_platform_ok = check_client("ZTNA-Platform-realm", clients)
    print()
    
    # Check audience mappers
    print("Checking audience mappers...\n")
    if admin_frontend_ok:
        check_audience_mapper(token, "admin-frontend")
        print()
    
    # Test token issuance
    print("Testing token issuance...\n")
    try:
        # Try to get a token using admin-frontend client
        response = requests.post(
            f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
            data={
                "username": ADMIN_USER,
                "password": ADMIN_PASSWORD,
                "grant_type": "password",
                "client_id": "admin-frontend"
            },
            timeout=10
        )
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if access_token:
                # Decode token to check issuer and audience
                import base64
                import json
                parts = access_token.split('.')
                if len(parts) >= 2:
                    payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
                    issuer = payload.get("iss")
                    audience = payload.get("aud")
                    print(f"✅ Token issued successfully")
                    print(f"   Issuer: {issuer}")
                    print(f"   Audience: {audience}")
                    print(f"   Expected issuer: {KEYCLOAK_URL}/realms/{REALM}")
                    if issuer == f"{KEYCLOAK_URL}/realms/{REALM}":
                        print(f"   ✅ Issuer matches")
                    else:
                        print(f"   ⚠️  Issuer mismatch (this might be OK if using different hostname)")
                    if isinstance(audience, list) and "admin-frontend" in audience:
                        print(f"   ✅ Audience includes 'admin-frontend'")
                    elif audience == "admin-frontend":
                        print(f"   ✅ Audience is 'admin-frontend'")
                    else:
                        print(f"   ⚠️  Audience doesn't include 'admin-frontend': {audience}")
        else:
            print(f"❌ Failed to get token: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing token issuance: {e}")
    
    print("\n" + "="*50)
    if admin_frontend_ok and ztna_platform_ok:
        print("✅ Keycloak configuration looks good!")
    else:
        print("⚠️  Some issues found. Please review the output above.")

if __name__ == "__main__":
    main()

