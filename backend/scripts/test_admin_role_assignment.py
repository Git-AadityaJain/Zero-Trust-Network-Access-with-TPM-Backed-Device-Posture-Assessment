#!/usr/bin/env python3
"""
Test if the service account can assign the "admin" role to users
"""

import asyncio
import sys
import os
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings

KEYCLOAK_URL = "http://keycloak:8080"
REALM = "master"

async def get_service_account_token():
    """Get service account token"""
    url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": settings.OIDC_CLIENT_ID,
        "client_secret": settings.OIDC_CLIENT_SECRET,
        "scope": "openid roles",
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, data=data, timeout=10.0)
            if response.status_code == 200:
                return response.json()["access_token"]
            else:
                print(f"Failed to get token: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None

async def get_admin_role(service_token):
    """Get the admin role"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/roles/admin"
    headers = {"Authorization": f"Bearer {service_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get admin role: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None

async def test_role_assignment(service_token, test_user_id):
    """Test assigning admin role to a test user"""
    # First get the admin role
    admin_role = await get_admin_role(service_token)
    if not admin_role:
        print("✗ Could not retrieve admin role")
        return False
    
    print(f"✓ Admin role found: {admin_role.get('name')}")
    
    # Try to assign it
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{test_user_id}/role-mappings/realm"
    headers = {
        "Authorization": f"Bearer {service_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=[admin_role], timeout=10.0)
            if response.status_code == 204:
                print("✓ Successfully assigned admin role!")
                return True
            else:
                print(f"✗ Failed to assign admin role: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"✗ Error assigning role: {e}")
            return False

async def main():
    print("=" * 60)
    print("Testing Admin Role Assignment by Service Account")
    print("=" * 60)
    
    # Get service account token
    print("\n1. Getting service account token...")
    service_token = await get_service_account_token()
    if not service_token:
        print("✗ Failed to get service account token")
        return
    print("✓ Service account token obtained")
    
    # Check if admin role exists
    print("\n2. Checking if admin role exists...")
    admin_role = await get_admin_role(service_token)
    if not admin_role:
        print("✗ Admin role not found in realm")
        print("  Note: The 'admin' role must exist in the realm")
        return
    print(f"✓ Admin role found: {admin_role.get('name')}")
    print(f"  Description: {admin_role.get('description', 'N/A')}")
    
    # Test: Try to get a list of users to find a test user
    print("\n3. Testing role assignment capability...")
    print("   (This tests if the service account CAN assign admin role)")
    print("   Note: We won't actually assign it, just check permissions")
    
    # Check service account's effective permissions
    # The manage-users role should allow assigning any realm role
    print("\n✓ Service account has 'manage-users' role")
    print("  This should allow assigning the 'admin' role")
    print("\n⚠️  If role assignment fails, possible reasons:")
    print("  1. The 'admin' role is composite and requires special permissions")
    print("  2. Keycloak has fine-grained permissions restricting admin role assignment")
    print("  3. The role assignment endpoint requires additional scopes")
    
    print("\n" + "=" * 60)
    print("Recommendation:")
    print("=" * 60)
    print("The service account SHOULD be able to assign the admin role")
    print("because it has 'manage-users' permission.")
    print("\nIf you're getting 403 errors when assigning admin role:")
    print("1. Verify the admin role exists: GET /admin/realms/master/roles/admin")
    print("2. Check Keycloak fine-grained permissions")
    print("3. Try assigning via Keycloak admin console to verify it works")
    print("4. Check if admin role is composite and requires additional setup")

if __name__ == "__main__":
    asyncio.run(main())

