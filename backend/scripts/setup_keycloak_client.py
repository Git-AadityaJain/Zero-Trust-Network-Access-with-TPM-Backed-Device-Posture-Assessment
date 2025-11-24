#!/usr/bin/env python3
"""
Script to configure Keycloak client for backend service account authentication
This script will:
1. Check if ZTNA-Platform-realm client exists
2. Enable service accounts
3. Generate/retrieve client secret
4. Configure the client properly
"""

import asyncio
import sys
import os
import httpx
import base64

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

KEYCLOAK_URL = str(settings.OIDC_ISSUER).split('/realms/')[0]  # http://keycloak:8080
REALM = "master"
CLIENT_ID = "ZTNA-Platform-realm"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin"  # Default Keycloak admin password

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
        response = await client.post(url, data=data, timeout=10.0)
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Failed to get admin token: {response.status_code} - {response.text}")
            return None

async def get_client(admin_token):
    """Get client by ID"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params={"clientId": CLIENT_ID}, timeout=10.0)
        if response.status_code == 200:
            clients = response.json()
            return clients[0] if clients else None
        else:
            print(f"Failed to get client: {response.status_code} - {response.text}")
            return None

async def update_client(admin_token, client_id, updates):
    """Update client configuration"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_id}"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=updates, timeout=10.0)
        if response.status_code == 204:
            return True
        else:
            print(f"Failed to update client: {response.status_code} - {response.text}")
            return False

async def get_client_secret(admin_token, client_id):
    """Get client secret"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_id}/client-secret"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=10.0)
        if response.status_code == 200:
            return response.json().get("value")
        else:
            print(f"Failed to get client secret: {response.status_code} - {response.text}")
            return None

async def regenerate_client_secret(admin_token, client_id):
    """Regenerate client secret"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_id}/client-secret"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, timeout=10.0)
        if response.status_code == 200:
            return response.json().get("value")
        else:
            print(f"Failed to regenerate client secret: {response.status_code} - {response.text}")
            return None

async def setup_client():
    """Main setup function"""
    print("=" * 60)
    print("Keycloak Client Setup Script")
    print("=" * 60)
    
    # Get admin token
    print("\n1. Getting admin token...")
    admin_token = await get_admin_token()
    if not admin_token:
        print("✗ Failed to get admin token. Make sure Keycloak is running and admin credentials are correct.")
        return False
    print("✓ Admin token obtained")
    
    # Get client
    print(f"\n2. Getting client '{CLIENT_ID}'...")
    client = await get_client(admin_token)
    if not client:
        print(f"✗ Client '{CLIENT_ID}' not found. Please create it in Keycloak first.")
        return False
    print(f"✓ Client found (ID: {client['id']})")
    
    # Check current configuration
    print("\n3. Checking current configuration...")
    needs_update = False
    updates = {}
    
    if not client.get("serviceAccountsEnabled", False):
        print("  - Service accounts are disabled")
        updates["serviceAccountsEnabled"] = True
        needs_update = True
    
    if client.get("bearerOnly", False):
        print("  - Client is bearer-only (needs to be disabled for service accounts)")
        updates["bearerOnly"] = False
        needs_update = True
    
    if client.get("standardFlowEnabled", True):
        print("  - Standard flow is enabled (not needed for service accounts)")
        updates["standardFlowEnabled"] = False
        needs_update = True
    
    # Update client if needed
    if needs_update:
        print("\n4. Updating client configuration...")
        if await update_client(admin_token, client["id"], updates):
            print("✓ Client updated successfully")
        else:
            print("✗ Failed to update client")
            return False
    else:
        print("✓ Client configuration is correct")
    
    # Get or generate client secret
    print("\n5. Getting client secret...")
    secret = await get_client_secret(admin_token, client["id"])
    
    if not secret:
        print("  - No secret found, generating new one...")
        secret = await regenerate_client_secret(admin_token, client["id"])
    
    if secret:
        print(f"✓ Client secret obtained: {secret[:20]}...")
        print("\n" + "=" * 60)
        print("IMPORTANT: Update your backend/.env file with:")
        print(f"OIDC_CLIENT_SECRET={secret}")
        print("=" * 60)
        return True
    else:
        print("✗ Failed to get/generate client secret")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_client())
    sys.exit(0 if success else 1)

