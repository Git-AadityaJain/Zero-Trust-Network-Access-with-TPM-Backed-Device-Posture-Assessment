#!/usr/bin/env python3
"""
Script to assign required roles to the ZTNA-Platform-realm service account
This enables the service account to create/manage users via Keycloak Admin API
"""

import asyncio
import sys
import os
import httpx
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
REALM = "master"
CLIENT_ID = "ZTNA-Platform-realm"
ADMIN_USER = os.getenv("KEYCLOAK_ADMIN", "admin")
ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "adminsecure123")

# Required roles for service account to manage users
REQUIRED_CLIENT_ROLES = [
    "manage-users",      # Create, update, delete users
    "view-users",        # View user details
    "query-users",       # Search users
    "manage-realm",      # General realm management
    "view-realm"         # View realm settings
]

# In master realm, the management client is called "master-realm"
# In other realms, it's called "realm-management"
REALM_MANAGEMENT_CLIENT = "master-realm"

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
            print(f"Error getting client ID: {e}")
            return None

async def get_service_account_user_id(admin_token, client_id):
    """Get the service account user ID for a client"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_id}/service-account-user"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                return response.json()["id"]
            else:
                print(f"Failed to get service account user: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error getting service account user: {e}")
            return None

async def get_client_roles(admin_token, client_id, role_names):
    """Get client role objects by name"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_id}/roles"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    roles = []
    async with httpx.AsyncClient() as client:
        for role_name in role_names:
            try:
                response = await client.get(
                    f"{url}/{role_name}",
                    headers=headers,
                    timeout=10.0
                )
                if response.status_code == 200:
                    roles.append(response.json())
                else:
                    print(f"Warning: Role '{role_name}' not found (status: {response.status_code})")
            except Exception as e:
                print(f"Error getting role '{role_name}': {e}")
    
    return roles

async def assign_roles_to_user(admin_token, user_id, client_id, roles):
    """Assign client roles to a user"""
    # The endpoint requires the client ID in the URL path
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}/role-mappings/clients/{client_id}"
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=roles, timeout=10.0)
            if response.status_code == 204:
                return True
            else:
                print(f"Failed to assign roles: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Error assigning roles: {e}")
            return False

async def main():
    """Main function"""
    print("=" * 60)
    print("Assigning Roles to Service Account")
    print("=" * 60)
    
    # Step 1: Get admin token
    print("\n1. Getting admin token...")
    admin_token = await get_admin_token()
    if not admin_token:
        print("✗ Failed to get admin token")
        return False
    print("✓ Admin token obtained")
    
    # Step 2: Get ZTNA-Platform-realm client ID
    print(f"\n2. Getting client ID for '{CLIENT_ID}'...")
    client_id = await get_client_id(admin_token, CLIENT_ID)
    if not client_id:
        print(f"✗ Client '{CLIENT_ID}' not found")
        return False
    print(f"✓ Client found (ID: {client_id})")
    
    # Step 3: Get service account user ID
    print(f"\n3. Getting service account user for '{CLIENT_ID}'...")
    service_account_user_id = await get_service_account_user_id(admin_token, client_id)
    if not service_account_user_id:
        print("✗ Failed to get service account user")
        print("  Make sure service accounts are enabled for this client")
        return False
    print(f"✓ Service account user found (ID: {service_account_user_id})")
    
    # Step 4: Get realm-management client ID (master-realm in master realm)
    print(f"\n4. Getting '{REALM_MANAGEMENT_CLIENT}' client ID...")
    realm_mgmt_client_id = await get_client_id(admin_token, REALM_MANAGEMENT_CLIENT)
    if not realm_mgmt_client_id:
        # Try alternative name
        if REALM_MANAGEMENT_CLIENT == "master-realm":
            print("  Trying 'realm-management' as alternative...")
            realm_mgmt_client_id = await get_client_id(admin_token, "realm-management")
        if not realm_mgmt_client_id:
            print(f"✗ Client '{REALM_MANAGEMENT_CLIENT}' not found")
            print("  Note: In master realm, the management client is 'master-realm'")
            return False
    print(f"✓ Realm-management client found (ID: {realm_mgmt_client_id})")
    
    # Step 5: Get required roles
    print(f"\n5. Getting required roles from '{REALM_MANAGEMENT_CLIENT}'...")
    roles = await get_client_roles(admin_token, realm_mgmt_client_id, REQUIRED_CLIENT_ROLES)
    if not roles:
        print("✗ No roles found")
        return False
    
    found_roles = [r["name"] for r in roles]
    print(f"✓ Found {len(roles)} roles: {', '.join(found_roles)}")
    
    missing_roles = set(REQUIRED_CLIENT_ROLES) - set(found_roles)
    if missing_roles:
        print(f"⚠ Warning: Missing roles: {', '.join(missing_roles)}")
    
    # Step 6: Assign roles to service account
    print(f"\n6. Assigning roles to service account...")
    if await assign_roles_to_user(admin_token, service_account_user_id, realm_mgmt_client_id, roles):
        print("✓ Roles assigned successfully")
        print("\n" + "=" * 60)
        print("Service account is now configured with required permissions!")
        print("You can now create users via the backend API.")
        print("=" * 60)
        return True
    else:
        print("✗ Failed to assign roles")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

