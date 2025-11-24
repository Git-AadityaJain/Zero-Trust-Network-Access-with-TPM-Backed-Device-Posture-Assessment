#!/usr/bin/env python3
"""
Check if roles are actually assigned to service account in Keycloak
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

async def get_user_roles(admin_token, user_id, client_id):
    """Get roles assigned to user for a specific client"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}/role-mappings/clients/{client_id}"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []

async def main():
    print("=" * 60)
    print("Checking Service Account Roles in Keycloak")
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
    print(f"✓ Client found")
    
    print("\n2. Getting service account user...")
    user_id = await get_service_account_user_id(admin_token, client_id)
    if not user_id:
        print("✗ Service account not found")
        return
    print(f"✓ Service account user found: {user_id}")
    
    print("\n3. Getting master-realm client ID...")
    master_realm_client_id = await get_client_id(admin_token, "master-realm")
    if not master_realm_client_id:
        print("✗ master-realm client not found")
        return
    print(f"✓ master-realm client found: {master_realm_client_id}")
    
    print("\n4. Checking assigned roles...")
    roles = await get_user_roles(admin_token, user_id, master_realm_client_id)
    
    if roles:
        print(f"✓ Found {len(roles)} assigned roles:")
        for role in roles:
            print(f"  - {role.get('name')}")
        
        required = ['manage-users', 'view-users', 'query-users']
        assigned_names = [r.get('name') for r in roles]
        
        print("\nRequired roles check:")
        for req in required:
            if req in assigned_names:
                print(f"  ✓ {req}")
            else:
                print(f"  ✗ {req} (MISSING)")
    else:
        print("✗ No roles assigned!")
        print("\nRun: docker exec -it ztna-backend python /app/scripts/assign_service_account_roles.py")

if __name__ == "__main__":
    asyncio.run(main())

