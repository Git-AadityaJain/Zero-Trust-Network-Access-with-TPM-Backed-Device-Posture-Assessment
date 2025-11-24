#!/usr/bin/env python3
"""
Script to create/configure the ZTNA-Platform-realm client in Keycloak
This ensures the client exists with proper service account configuration
"""

import asyncio
import sys
import os
import httpx
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KEYCLOAK_URL = "http://keycloak:8080"  # Internal Docker network
REALM = "master"
CLIENT_ID = "ZTNA-Platform-realm"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "adminsecure123"  # From docker-compose.yml

async def get_admin_token():
    """Get Keycloak admin token"""
    url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": ADMIN_USER,
        "password": ADMIN_PASSWORD
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, data=data, timeout=10.0)
            if response.status_code == 200:
                return response.json()["access_token"]
            else:
                print(f"Failed to get admin token: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error getting admin token: {e}")
            return None

async def client_exists(admin_token):
    """Check if client exists"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params={"clientId": CLIENT_ID}, timeout=10.0)
            if response.status_code == 200:
                clients = response.json()
                return clients[0] if clients else None
            return None
        except Exception as e:
            print(f"Error checking client: {e}")
            return None

async def create_client(admin_token):
    """Create the ZTNA-Platform-realm client"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients"
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    client_config = {
        "clientId": CLIENT_ID,
        "name": "ZTNA-Platform Realm",
        "enabled": True,
        "clientAuthenticatorType": "client-secret",
        "redirectUris": [],
        "webOrigins": [],
        "bearerOnly": False,
        "consentRequired": False,
        "standardFlowEnabled": False,
        "implicitFlowEnabled": False,
        "directAccessGrantsEnabled": False,
        "serviceAccountsEnabled": True,
        "publicClient": False,
        "frontchannelLogout": False,
        "protocol": "openid-connect",
        "attributes": {},
        "fullScopeAllowed": False
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=client_config, timeout=10.0)
            if response.status_code == 201:
                print(f"✓ Client '{CLIENT_ID}' created successfully")
                return True
            else:
                print(f"Failed to create client: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Error creating client: {e}")
            return False

async def update_client(admin_token, client_id):
    """Update client to ensure service accounts are enabled"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_id}"
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    updates = {
        "serviceAccountsEnabled": True,
        "bearerOnly": False,
        "standardFlowEnabled": False
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(url, headers=headers, json=updates, timeout=10.0)
            if response.status_code == 204:
                print(f"✓ Client '{CLIENT_ID}' updated successfully")
                return True
            else:
                print(f"Failed to update client: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Error updating client: {e}")
            return False

async def get_client_secret(admin_token, client_id):
    """Get or generate client secret"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_id}/client-secret"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            # Try to get existing secret
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                secret_data = response.json()
                if secret_data.get("value"):
                    return secret_data["value"]
            
            # If no secret, generate one
            response = await client.post(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                secret_data = response.json()
                return secret_data.get("value")
            
            return None
        except Exception as e:
            print(f"Error getting/generating secret: {e}")
            return None

async def main():
    """Main function"""
    print("=" * 60)
    print("Keycloak Client Setup - ZTNA-Platform-realm")
    print("=" * 60)
    
    # Get admin token
    print("\n1. Getting admin token...")
    admin_token = await get_admin_token()
    if not admin_token:
        print("✗ Failed to get admin token")
        print("  Make sure Keycloak is running and admin credentials are correct")
        return False
    print("✓ Admin token obtained")
    
    # Check if client exists
    print(f"\n2. Checking if client '{CLIENT_ID}' exists...")
    client = await client_exists(admin_token)
    
    if not client:
        print(f"  Client not found, creating...")
        if await create_client(admin_token):
            # Get the newly created client
            client = await client_exists(admin_token)
        else:
            print("✗ Failed to create client")
            return False
    else:
        print(f"✓ Client found (ID: {client['id']})")
        
        # Check if service accounts are enabled
        if not client.get("serviceAccountsEnabled", False):
            print("  Service accounts disabled, updating...")
            await update_client(admin_token, client["id"])
            client = await client_exists(admin_token)
    
    # Get or generate secret
    print(f"\n3. Getting client secret...")
    secret = await get_client_secret(admin_token, client["id"])
    
    if secret:
        print(f"✓ Client secret obtained")
        print("\n" + "=" * 60)
        print("IMPORTANT: Add this to your backend/.env file:")
        print(f"OIDC_CLIENT_SECRET={secret}")
        print("=" * 60)
        return True
    else:
        print("✗ Failed to get/generate client secret")
        print("  You may need to generate it manually in Keycloak Admin Console")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

