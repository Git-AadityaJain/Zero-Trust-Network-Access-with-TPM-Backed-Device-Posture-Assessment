#!/usr/bin/env python3
"""
Update ZTNA-Platform-realm client to enable fullScopeAllowed
"""

import asyncio
import sys
import os
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KEYCLOAK_URL = "http://keycloak:8080"
REALM = "master"
CLIENT_ID = "ZTNA-Platform-realm"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "adminsecure123"

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
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

async def get_client_id(admin_token, client_name):
    """Get client's internal ID"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params={"clientId": client_name}, timeout=10.0)
            if response.status_code == 200:
                clients = response.json()
                return clients[0]["id"] if clients else None
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

async def update_client(admin_token, client_id):
    """Update client to enable fullScopeAllowed"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_id}"
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    # Get current client config first
    async with httpx.AsyncClient() as client:
        try:
            get_response = await client.get(url, headers=headers, timeout=10.0)
            if get_response.status_code != 200:
                print(f"Failed to get client: {get_response.status_code}")
                return False
            
            client_data = get_response.json()
            client_data["fullScopeAllowed"] = True
            
            # Update client
            put_response = await client.put(url, headers=headers, json=client_data, timeout=10.0)
            if put_response.status_code == 204:
                return True
            else:
                print(f"Failed to update client: {put_response.status_code} - {put_response.text}")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False

async def main():
    print("=" * 60)
    print("Updating Client Configuration")
    print("=" * 60)
    
    admin_token = await get_admin_token()
    if not admin_token:
        print("✗ Failed to get admin token")
        return False
    
    print("\n1. Getting client ID...")
    client_id = await get_client_id(admin_token, CLIENT_ID)
    if not client_id:
        print(f"✗ Client '{CLIENT_ID}' not found")
        return False
    print(f"✓ Client found")
    
    print("\n2. Updating client to enable fullScopeAllowed...")
    if await update_client(admin_token, client_id):
        print("✓ Client updated successfully!")
        print("\nNow restart the backend and get a new token.")
        return True
    else:
        print("✗ Failed to update client")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

