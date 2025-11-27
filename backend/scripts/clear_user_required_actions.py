#!/usr/bin/env python3
"""
Clear required actions (like UPDATE_PASSWORD) for a Keycloak user.
This fixes the redirect loop issue after password reset.
"""
import asyncio
import httpx
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

async def find_user_by_username(admin_token, username):
    """Find user by username"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    params = {"username": username, "exact": "true"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=10.0)
            if response.status_code == 200:
                users = response.json()
                return users[0] if users else None
            else:
                print(f"Failed to find user: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error finding user: {e}")
            return None

async def clear_required_actions(admin_token, user_id):
    """Clear all required actions for a user"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}/execute-actions-email"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    # First, get user details to see required actions
    user_url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            # Get user details
            response = await client.get(user_url, headers=headers, timeout=10.0)
            if response.status_code != 200:
                print(f"Failed to get user details: {response.status_code}")
                return False
            
            user_data = response.json()
            required_actions = user_data.get("requiredActions", [])
            
            if not required_actions:
                print("No required actions to clear")
                return True
            
            print(f"Found required actions: {required_actions}")
            
            # Clear required actions by updating user
            # Remove requiredActions from the update payload (Keycloak will clear them)
            update_data = {
                "username": user_data.get("username"),
                "email": user_data.get("email"),
                "firstName": user_data.get("firstName"),
                "lastName": user_data.get("lastName"),
                "enabled": user_data.get("enabled", True),
                "requiredActions": []  # Clear all required actions
            }
            
            # Update user
            response = await client.put(user_url, headers=headers, json=update_data, timeout=10.0)
            if response.status_code == 204:
                print(f"[OK] Cleared required actions for user")
                return True
            else:
                print(f"Failed to clear required actions: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error clearing required actions: {e}")
            return False

async def main():
    if len(sys.argv) < 2:
        print("Usage: python clear_user_required_actions.py <username>")
        print("Example: python clear_user_required_actions.py testuser")
        sys.exit(1)
    
    username = sys.argv[1]
    
    print("=" * 60)
    print("Clear Keycloak User Required Actions")
    print("=" * 60)
    print()
    
    # Detect if running on host or in Docker
    if os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER"):
        keycloak_host = "http://keycloak:8080"
    else:
        keycloak_host = KEYCLOAK_URL
    
    print(f"Connecting to Keycloak at: {keycloak_host}")
    print(f"Realm: {REALM}")
    print(f"Username: {username}")
    print()
    
    # Get admin token
    print("1. Getting admin token...")
    admin_token = await get_admin_token()
    if not admin_token:
        print("[ERROR] Failed to get admin token. Make sure Keycloak is running.")
        sys.exit(1)
    
    print("   [OK] Admin token obtained")
    print()
    
    # Find user
    print(f"2. Finding user '{username}'...")
    user = await find_user_by_username(admin_token, username)
    if not user:
        print(f"[ERROR] User '{username}' not found")
        sys.exit(1)
    
    print(f"   [OK] Found user: {user.get('id')}")
    print()
    
    # Clear required actions
    print("3. Clearing required actions...")
    success = await clear_required_actions(admin_token, user["id"])
    
    if success:
        print()
        print("=" * 60)
        print("[OK] Required actions cleared successfully!")
        print("=" * 60)
        print()
        print("The user can now log in without being forced to change password.")
        return True
    else:
        print()
        print("=" * 60)
        print("[ERROR] Failed to clear required actions!")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

