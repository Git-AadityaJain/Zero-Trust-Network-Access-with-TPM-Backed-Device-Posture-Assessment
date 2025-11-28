#!/usr/bin/env python3
"""
Verify the format of post-logout redirect URIs in Keycloak
"""

import asyncio
import sys
import os
import httpx

KEYCLOAK_URL = "https://unimplied-untranscendental-denita.ngrok-free.dev/auth"
REALM = "master"
CLIENT_ID = "admin-frontend"
ADMIN_USER = "admin"
ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "adminsecure123")

async def get_admin_token():
    """Get admin token"""
    url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
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
                print(f"[ERROR] Failed to get admin token: {response.status_code}")
                return None
        except Exception as e:
            print(f"[ERROR] Error getting admin token: {e}")
            return None

async def get_client(admin_token):
    """Get client configuration"""
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
            print(f"[ERROR] Error getting client: {e}")
            return None

async def main():
    print("=" * 70)
    print("Verify Post-Logout Redirect URIs Format")
    print("=" * 70)
    print()
    
    admin_token = await get_admin_token()
    if not admin_token:
        print("[ERROR] Failed to get admin token")
        sys.exit(1)
    
    client = await get_client(admin_token)
    if not client:
        print(f"[ERROR] Client '{CLIENT_ID}' not found")
        sys.exit(1)
    
    # Get the stored value
    stored_value = client.get("attributes", {}).get("post.logout.redirect.uris", "")
    
    print(f"Stored value in Keycloak:")
    print(f"  Raw: {repr(stored_value)}")
    print()
    
    # Parse it
    if stored_value:
        uris = [uri.strip() for uri in stored_value.split(",") if uri.strip()]
        print(f"Parsed URIs ({len(uris)}):")
        for i, uri in enumerate(uris, 1):
            print(f"  {i}. {uri}")
    else:
        print("  (empty)")
    
    print()
    print("Note: Keycloak Admin Console should display these in separate fields.")
    print("If you see them in a single text box, refresh the page or check Keycloak version.")

if __name__ == "__main__":
    asyncio.run(main())

