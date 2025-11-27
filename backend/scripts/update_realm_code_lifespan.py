#!/usr/bin/env python3
"""
Update Keycloak realm access code lifespan settings.
This fixes expired_code errors during password reset flows.
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
REALM = "master"
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

async def update_realm_settings(admin_token):
    """Update realm access code lifespan settings"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}"
    
    # Get current realm settings
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Get current realm config
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code != 200:
                print(f"Failed to get realm settings: {response.status_code} - {response.text}")
                return False
            
            realm_data = response.json()
            
            # Update access code lifespan settings
            # Increase significantly to handle password reset flows
            realm_data["accessCodeLifespan"] = 600  # 10 minutes (was 60 seconds)
            realm_data["accessCodeLifespanUserAction"] = 1200  # 20 minutes (was 300 seconds)
            # accessCodeLifespanLogin stays at 1800 (30 minutes)
            
            # Update realm
            response = await client.put(url, headers=headers, json=realm_data, timeout=10.0)
            if response.status_code == 204:
                print("[OK] Successfully updated realm access code lifespan settings:")
                print(f"   - accessCodeLifespan: 60 -> 600 seconds (10 minutes)")
                print(f"   - accessCodeLifespanUserAction: 300 -> 1200 seconds (20 minutes)")
                return True
            else:
                print(f"Failed to update realm settings: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error updating realm settings: {e}")
            return False

async def main():
    print("=" * 60)
    print("Keycloak Realm Access Code Lifespan Update")
    print("=" * 60)
    print()
    
    # Detect if running on host or in Docker
    if os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER"):
        keycloak_host = "http://keycloak:8080"
    else:
        keycloak_host = KEYCLOAK_URL
    
    print(f"Connecting to Keycloak at: {keycloak_host}")
    print(f"Realm: {REALM}")
    print()
    
    # Get admin token
    print("1. Getting admin token...")
    admin_token = await get_admin_token()
    if not admin_token:
        print("[ERROR] Failed to get admin token. Make sure Keycloak is running.")
        return False
    
    print("   [OK] Admin token obtained")
    print()
    
    # Update realm settings
    print("2. Updating realm access code lifespan settings...")
    success = await update_realm_settings(admin_token)
    
    if success:
        print()
        print("=" * 60)
        print("[OK] Update completed successfully!")
        print("=" * 60)
        print()
        print("The new settings allow more time for password reset flows.")
        print("Users should now be able to complete password resets without")
        print("encountering 'expired_code' errors.")
        return True
    else:
        print()
        print("=" * 60)
        print("[ERROR] Update failed!")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

