#!/usr/bin/env python3
"""
Test script for single-session-per-user enforcement
This script helps verify that the feature is working correctly
"""

import asyncio
import sys
import os
import httpx
import json
from datetime import datetime

KEYCLOAK_URL = "https://unimplied-untranscendental-denita.ngrok-free.dev/auth"
API_URL = "https://unimplied-untranscendental-denita.ngrok-free.dev/api"
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


async def get_user_id(admin_token, username):
    """Get user ID by username"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params={"username": username, "exact": "true"}, timeout=10.0)
            if response.status_code == 200:
                users = response.json()
                if users and len(users) > 0:
                    return users[0]["id"]
                return None
            return None
        except Exception as e:
            print(f"[ERROR] Error getting user ID: {e}")
            return None


async def get_user_sessions(admin_token, user_id):
    """Get all sessions for a user"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}/sessions"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[ERROR] Failed to get sessions: {response.status_code}")
                return []
        except Exception as e:
            print(f"[ERROR] Error getting sessions: {e}")
            return []


async def get_session_info(access_token):
    """Get session info from API"""
    url = f"{API_URL}/session/info"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[ERROR] Failed to get session info: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"[ERROR] Error getting session info: {e}")
            return None


async def enforce_single_session(access_token):
    """Call enforce-single endpoint"""
    url = f"{API_URL}/session/enforce-single"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[ERROR] Failed to enforce single session: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"[ERROR] Error enforcing single session: {e}")
            return None


def decode_token(token):
    """Decode JWT token to get payload"""
    try:
        import base64
        parts = token.split('.')
        if len(parts) != 3:
            return None
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        print(f"[ERROR] Failed to decode token: {e}")
        return None


async def main():
    print("=" * 70)
    print("Single-Session-Per-User Feature Test")
    print("=" * 70)
    print()
    
    # Get admin token
    print("Step 1: Getting admin token...")
    admin_token = await get_admin_token()
    if not admin_token:
        print("[ERROR] Failed to get admin token")
        sys.exit(1)
    print("[OK] Admin token obtained")
    print()
    
    # Get user ID
    try:
        username = input("Enter username to test (default: admin-user): ").strip() or "admin-user"
    except EOFError:
        # Non-interactive environment, use default
        username = "admin-user"
        print(f"Using default username: {username}")
    print(f"\nStep 2: Getting user ID for '{username}'...")
    user_id = await get_user_id(admin_token, username)
    if not user_id:
        print(f"[ERROR] User '{username}' not found")
        sys.exit(1)
    print(f"[OK] User ID: {user_id}")
    print()
    
    # Get current sessions
    print("Step 3: Checking current sessions...")
    sessions = await get_user_sessions(admin_token, user_id)
    print(f"[INFO] User has {len(sessions)} active session(s)")
    
    if sessions:
        print("\nActive Sessions:")
        for i, session in enumerate(sessions, 1):
            print(f"  {i}. Session ID: {session.get('id', 'N/A')}")
            print(f"     Started: {datetime.fromtimestamp(session.get('start', 0) / 1000) if session.get('start') else 'N/A'}")
            print(f"     Last Access: {datetime.fromtimestamp(session.get('lastAccess', 0) / 1000) if session.get('lastAccess') else 'N/A'}")
            print(f"     Clients: {', '.join(session.get('clients', {}).keys())}")
            print()
    else:
        print("[INFO] No active sessions found")
        print()
    
    # Test with access token
    print("=" * 70)
    print("API Testing")
    print("=" * 70)
    print()
    print("To test the API endpoints, you need a valid access token.")
    print("You can get one by:")
    print("1. Logging in through the frontend")
    print("2. Opening browser DevTools > Application > Local Storage")
    print("3. Copy the 'access_token' value")
    print()
    
    try:
        access_token = input("Enter access token (or press Enter to skip API testing): ").strip()
    except EOFError:
        # Non-interactive environment, skip API testing
        access_token = ""
        print("Skipping API testing (non-interactive environment)")
    
    if access_token:
        print()
        print("Step 4: Testing session info endpoint...")
        session_info = await get_session_info(access_token)
        if session_info:
            print("[OK] Session info retrieved:")
            print(f"   User ID: {session_info.get('user_id')}")
            print(f"   Session Count: {session_info.get('session_count')}")
            print(f"   Message: {session_info.get('message')}")
            print()
            
            # Decode token to show session ID
            token_payload = decode_token(access_token)
            if token_payload:
                print("Token Information:")
                print(f"   User ID (sub): {token_payload.get('sub')}")
                print(f"   Session ID (sid): {token_payload.get('sid', 'Not present')}")
                print(f"   Expires: {datetime.fromtimestamp(token_payload.get('exp', 0))}")
                print()
        
        print("Step 5: Testing enforce-single endpoint...")
        enforce_result = await enforce_single_session(access_token)
        if enforce_result:
            print("[OK] Single session enforcement result:")
            print(f"   User ID: {enforce_result.get('user_id')}")
            print(f"   Session Count: {enforce_result.get('session_count')}")
            print(f"   Logged Out Count: {enforce_result.get('logged_out_count')}")
            print(f"   Message: {enforce_result.get('message')}")
            print()
            
            # Check sessions again
            print("Step 6: Verifying sessions after enforcement...")
            sessions_after = await get_user_sessions(admin_token, user_id)
            print(f"[INFO] User now has {len(sessions_after)} active session(s)")
            if len(sessions_after) < len(sessions):
                print(f"[OK] Sessions reduced from {len(sessions)} to {len(sessions_after)}")
            elif len(sessions_after) == len(sessions):
                print("[WARNING] Session count did not change")
            print()
    else:
        print("[SKIP] API testing skipped")
        print()
    
    print("=" * 70)
    print("Manual Testing Instructions")
    print("=" * 70)
    print()
    print("To manually test the feature:")
    print()
    print("1. Open Browser A (e.g., Chrome)")
    print("   - Navigate to the frontend URL")
    print("   - Log in with username:", username)
    print("   - Verify you can access the dashboard")
    print()
    print("2. Open Browser B (e.g., Firefox or Incognito)")
    print("   - Navigate to the frontend URL")
    print("   - Log in with the same username:", username)
    print("   - Verify you can access the dashboard")
    print()
    print("3. Go back to Browser A")
    print("   - Refresh the page")
    print("   - You should be redirected to the login page")
    print("   - This confirms the session was terminated")
    print()
    print("4. Verify Browser B is still active")
    print("   - Refresh Browser B")
    print("   - You should still be logged in")
    print("   - This confirms only one session remains active")
    print()
    print("5. Check backend logs")
    print("   - Look for 'Enforced single session' messages")
    print("   - Verify session count and logged out count")
    print()


if __name__ == "__main__":
    asyncio.run(main())

