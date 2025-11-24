#!/usr/bin/env python3
"""
Force Keycloak to refresh service account token by invalidating existing sessions
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

async def get_service_account_user_id(admin_token, client_id):
    """Get the service account user ID"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_id}/service-account-user"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                return response.json()["id"]
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

async def logout_user(admin_token, user_id):
    """Logout user to force token refresh"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}/logout"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, timeout=10.0)
            return response.status_code in [204, 404]  # 404 means no active sessions
        except Exception as e:
            print(f"Error: {e}")
            return False

async def main():
    print("=" * 60)
    print("Forcing Service Account Token Refresh")
    print("=" * 60)
    
    admin_token = await get_admin_token()
    if not admin_token:
        print("✗ Failed to get admin token")
        return
    
    print("\n1. Getting client ID...")
    client_id = await get_client_id(admin_token, CLIENT_ID)
    if not client_id:
        print(f"✗ Client '{CLIENT_ID}' not found")
        return
    
    print("\n2. Getting service account user...")
    user_id = await get_service_account_user_id(admin_token, client_id)
    if not user_id:
        print("✗ Service account not found")
        return
    
    print(f"\n3. Logging out service account to invalidate sessions...")
    if await logout_user(admin_token, user_id):
        print("✓ Service account logged out")
        print("\nNext token request will include the new roles.")
    else:
        print("⚠ Could not logout (may have no active sessions)")

if __name__ == "__main__":
    asyncio.run(main())

