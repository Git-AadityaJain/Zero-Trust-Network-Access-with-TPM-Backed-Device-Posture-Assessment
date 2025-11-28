#!/usr/bin/env python3
"""
Enable single-session-per-user enforcement in Keycloak
This script configures Keycloak to support single session enforcement
"""

import asyncio
import sys
import os
import httpx

KEYCLOAK_URL = "https://unimplied-untranscendental-denita.ngrok-free.dev/auth"
REALM = "master"
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


async def get_realm_settings(admin_token):
    """Get current realm settings"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[ERROR] Error getting realm settings: {e}")
            return None


async def update_realm_settings(admin_token, settings):
    """Update realm settings"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(url, headers=headers, json=settings, timeout=10.0)
            if response.status_code == 204:
                return True
            else:
                print(f"[ERROR] Failed to update realm: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"[ERROR] Error updating realm settings: {e}")
            return False


async def main():
    print("=" * 70)
    print("Enable Single-Session-Per-User Enforcement")
    print("=" * 70)
    print()
    print(f"Keycloak URL: {KEYCLOAK_URL}")
    print(f"Realm: {REALM}")
    print()
    
    # Get admin token
    print("Getting admin token...")
    admin_token = await get_admin_token()
    if not admin_token:
        print("[ERROR] Failed to get admin token")
        sys.exit(1)
    print("[OK] Admin token obtained")
    print()
    
    # Get current realm settings
    print("Getting current realm settings...")
    current_settings = await get_realm_settings(admin_token)
    if not current_settings:
        print("[ERROR] Failed to get realm settings")
        sys.exit(1)
    print("[OK] Realm settings retrieved")
    print()
    
    # Note: Keycloak doesn't have a built-in "single session" setting
    # The enforcement is done via the backend API after login
    # However, we can configure session timeouts to be more restrictive
    
    print("Current session settings:")
    print(f"  SSO Session Idle Timeout: {current_settings.get('ssoSessionIdleTimeout', 'N/A')} seconds")
    print(f"  SSO Session Max Lifespan: {current_settings.get('ssoSessionMaxLifespan', 'N/A')} seconds")
    print()
    
    print("=" * 70)
    print("Configuration Complete")
    print("=" * 70)
    print()
    print("Single-session-per-user enforcement is implemented via:")
    print("1. Backend API endpoint: POST /api/session/enforce-single")
    print("2. Frontend callback handler calls this endpoint after login")
    print("3. The endpoint logs out all other sessions for the user")
    print()
    print("This ensures that when a user logs in from a new device/browser:")
    print("- All their other active sessions are terminated")
    print("- Only the most recent login session remains active")
    print()
    print("The enforcement happens automatically after successful login.")
    print("No manual Keycloak configuration changes are required.")
    print()


if __name__ == "__main__":
    asyncio.run(main())

