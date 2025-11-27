#!/usr/bin/env python3
"""
Get the client secret for ZTNA-Platform-realm client from Keycloak.
This script retrieves or generates the client secret needed for backend authentication.
"""
import asyncio
import sys
import os
import httpx

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
REALM = "master"
CLIENT_ID = "ZTNA-Platform-realm"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "adminsecure123"

async def get_admin_token():
    """Get admin access token"""
    url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
    data = {
        "username": ADMIN_USER,
        "password": ADMIN_PASSWORD,
        "grant_type": "password",
        "client_id": "admin-cli"
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

async def get_client(admin_token):
    """Get client by clientId"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    params = {"clientId": CLIENT_ID}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=10.0)
            if response.status_code == 200:
                clients = response.json()
                return clients[0] if clients else None
            else:
                print(f"Failed to get client: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error getting client: {e}")
            return None

async def get_client_secret(admin_token, client_uuid):
    """Get or generate client secret"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_uuid}/client-secret"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Try to get existing secret
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                secret_data = response.json()
                if secret_data.get("value"):
                    return secret_data["value"]
            
            # If no secret exists, generate a new one
            print("  No secret found, generating new one...")
            response = await client.post(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                secret_data = response.json()
                return secret_data.get("value")
            else:
                print(f"Failed to generate secret: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error getting/generating secret: {e}")
            return None

async def main():
    print("=" * 60)
    print("Get Keycloak Client Secret - ZTNA-Platform-realm")
    print("=" * 60)
    print()
    
    # Detect if running on host or in Docker
    if os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER"):
        keycloak_host = "http://keycloak:8080"
    else:
        keycloak_host = KEYCLOAK_URL
    
    print(f"Connecting to Keycloak at: {keycloak_host}")
    print(f"Realm: {REALM}")
    print(f"Client ID: {CLIENT_ID}")
    print()
    
    # Get admin token
    print("1. Getting admin token...")
    admin_token = await get_admin_token()
    if not admin_token:
        print("[ERROR] Failed to get admin token. Make sure Keycloak is running.")
        return False
    
    print("   [OK] Admin token obtained")
    print()
    
    # Get client
    print(f"2. Finding client '{CLIENT_ID}'...")
    client = await get_client(admin_token)
    if not client:
        print(f"[ERROR] Client '{CLIENT_ID}' not found!")
        print("        Run 'python backend/scripts/setup_keycloak_client.py' to create it.")
        return False
    
    print(f"   [OK] Found client (ID: {client['id']})")
    
    # Check if service accounts are enabled
    if not client.get("serviceAccountsEnabled", False):
        print("   [WARNING] Service accounts are not enabled for this client!")
        print("            The backend needs service accounts to authenticate.")
    print()
    
    # Get client secret
    print("3. Getting client secret...")
    secret = await get_client_secret(admin_token, client["id"])
    
    if secret:
        print("   [OK] Client secret obtained")
        print()
        print("=" * 60)
        print("Add this to your backend/.env file:")
        print("=" * 60)
        print(f"OIDC_CLIENT_SECRET={secret}")
        print("=" * 60)
        print()
        print("Then restart the backend service for changes to take effect.")
        return True
    else:
        print("   [ERROR] Failed to get/generate client secret")
        print("          You may need to generate it manually in Keycloak Admin Console:")
        print(f"          {keycloak_host}/auth/admin -> Clients -> {CLIENT_ID} -> Credentials")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

