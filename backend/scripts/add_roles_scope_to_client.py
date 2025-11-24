#!/usr/bin/env python3
"""
Add 'roles' scope to ZTNA-Platform-realm client default scopes
This ensures roles appear in service account tokens
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

async def get_default_scopes(admin_token, client_id):
    """Get default client scopes"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_id}/default-client-scopes"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                return [s["name"] for s in response.json()]
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []

async def add_default_scope(admin_token, client_id, scope_name):
    """Add a default client scope"""
    # First, get the scope ID
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/client-scopes"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params={"search": scope_name}, timeout=10.0)
            if response.status_code == 200:
                scopes = response.json()
                scope = next((s for s in scopes if s["name"] == scope_name), None)
                if not scope:
                    print(f"✗ Scope '{scope_name}' not found")
                    return False
                
                scope_id = scope["id"]
                
                # Add scope to client
                add_url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_id}/default-client-scopes/{scope_id}"
                add_response = await client.put(add_url, headers=headers, timeout=10.0)
                
                if add_response.status_code == 204:
                    return True
                else:
                    print(f"Failed to add scope: {add_response.status_code} - {add_response.text}")
                    return False
        except Exception as e:
            print(f"Error: {e}")
            return False

async def main():
    print("=" * 60)
    print("Adding 'roles' Scope to Client")
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
    
    print("\n2. Checking current default scopes...")
    current_scopes = await get_default_scopes(admin_token, client_id)
    print(f"Current scopes: {', '.join(current_scopes) if current_scopes else 'none'}")
    
    if "roles" in current_scopes:
        print("\n✓ 'roles' scope already assigned!")
        return True
    
    print("\n3. Adding 'roles' scope...")
    if await add_default_scope(admin_token, client_id, "roles"):
        print("✓ 'roles' scope added successfully!")
        print("\nNow restart the backend to get a fresh token with roles.")
        return True
    else:
        print("✗ Failed to add scope")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

