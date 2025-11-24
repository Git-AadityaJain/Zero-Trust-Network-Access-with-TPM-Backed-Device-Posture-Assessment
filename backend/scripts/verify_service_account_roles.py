#!/usr/bin/env python3
"""
Script to verify service account has the required roles
"""

import asyncio
import sys
import os
import httpx
import base64
import json

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
        "scope": "openid roles",  # Request roles scope
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

def decode_token(token):
    """Decode JWT token to see claims"""
    try:
        parts = token.split('.')
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '==').decode())
        return payload
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

async def main():
    print("=" * 60)
    print("Verifying Service Account Token and Roles")
    print("=" * 60)
    
    print("\n1. Getting service account token...")
    token = await get_service_account_token()
    if not token:
        print("✗ Failed to get token")
        return
    
    print("✓ Token obtained")
    
    print("\n2. Decoding token to check roles...")
    payload = decode_token(token)
    if not payload:
        print("✗ Failed to decode token")
        return
    
    print("\nToken Claims:")
    print(f"  Subject (user ID): {payload.get('sub')}")
    print(f"  Client ID: {payload.get('azp')}")
    print(f"  Issuer: {payload.get('iss')}")
    
    # Check realm roles
    realm_roles = payload.get('realm_access', {}).get('roles', [])
    print(f"\nRealm Roles ({len(realm_roles)}):")
    for role in realm_roles:
        print(f"  - {role}")
    
    # Check resource access (client roles)
    resource_access = payload.get('resource_access', {})
    print(f"\nResource Access (Client Roles):")
    for client_id, roles_data in resource_access.items():
        client_roles = roles_data.get('roles', [])
        print(f"  {client_id}: {', '.join(client_roles) if client_roles else 'none'}")
    
    # Check for required roles
    required_roles = ['manage-users', 'view-users', 'query-users']
    master_realm_roles = resource_access.get('master-realm', {}).get('roles', [])
    
    print(f"\nRequired Roles Check:")
    for role in required_roles:
        if role in master_realm_roles:
            print(f"  ✓ {role}")
        else:
            print(f"  ✗ {role} (MISSING)")
    
    if all(role in master_realm_roles for role in required_roles):
        print("\n✓ All required roles are present!")
        print("  The service account should be able to create users.")
    else:
        print("\n✗ Some required roles are missing!")
        print("  Run: docker exec -it ztna-backend python /app/scripts/assign_service_account_roles.py")

if __name__ == "__main__":
    asyncio.run(main())

