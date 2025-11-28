#!/usr/bin/env python3
"""
Fix logout redirect issue by verifying and updating post_logout_redirect_uris
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
FRONTEND_URL = "https://unimplied-untranscendental-denita.ngrok-free.dev"

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

async def update_client(admin_token, client_uuid):
    """Update client with correct post_logout_redirect_uris"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_uuid}"
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    # Get current config
    async with httpx.AsyncClient() as client:
        try:
            get_response = await client.get(url, headers=headers, timeout=10.0)
            if get_response.status_code != 200:
                print(f"[ERROR] Failed to get client config: {get_response.status_code}")
                return False
            
            current_config = get_response.json()
            
            # Ensure post.logout.redirect.uris includes the frontend login URL
            if "attributes" not in current_config:
                current_config["attributes"] = {}
            
            current_logout_uris = current_config["attributes"].get("post.logout.redirect.uris", "")
            # Handle both comma and ## separators - replace ## with comma first
            normalized = current_logout_uris.replace("##", ",")
            # Split by comma and clean up - remove all whitespace
            logout_uri_list = [uri.strip() for uri in normalized.split(",") if uri.strip()]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_uris = []
            for uri in logout_uri_list:
                # Clean URI - remove any extra whitespace
                clean_uri = uri.strip()
                if clean_uri and clean_uri not in seen:
                    seen.add(clean_uri)
                    unique_uris.append(clean_uri)
            logout_uri_list = unique_uris
            
            # Define the exact URIs we want (in order)
            desired_uris = [
                f"{FRONTEND_URL}/login",
                "http://localhost:3000/login",
                "http://localhost/login"
            ]
            
            # Build final list - add desired URIs first, then any others
            final_uri_list = []
            seen_final = set()
            
            # Add desired URIs first (in order)
            for uri in desired_uris:
                if uri not in seen_final:
                    final_uri_list.append(uri)
                    seen_final.add(uri)
            
            # Add any other existing URIs that aren't duplicates
            for uri in logout_uri_list:
                if uri not in seen_final:
                    final_uri_list.append(uri)
                    seen_final.add(uri)
            
            # Format as comma-separated string with NO spaces after commas
            # Keycloak expects: "uri1,uri2,uri3" (no spaces)
            formatted_uris = ",".join(final_uri_list)
            
            print(f"[INFO] Setting post-logout redirect URIs:")
            for uri in final_uri_list:
                print(f"   - {uri}")
            
            current_config["attributes"]["post.logout.redirect.uris"] = formatted_uris
            
            # Update client
            put_response = await client.put(url, headers=headers, json=current_config, timeout=10.0)
            if put_response.status_code == 204:
                print(f"[OK] Updated post-logout redirect URIs")
                print(f"   URIs: {', '.join(logout_uri_list)}")
                return True
            else:
                print(f"[ERROR] Failed to update client: {put_response.status_code}")
                print(f"   Response: {put_response.text}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error updating client: {e}")
            return False

async def main():
    print("=" * 70)
    print("Fix Logout Redirect Issue")
    print("=" * 70)
    print()
    print(f"Keycloak URL: {KEYCLOAK_URL}")
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"Client ID: {CLIENT_ID}")
    print()
    
    # Get admin token
    print("Getting admin token...")
    admin_token = await get_admin_token()
    if not admin_token:
        print("[ERROR] Failed to get admin token")
        sys.exit(1)
    print("[OK] Admin token obtained")
    print()
    
    # Get client
    print(f"Getting {CLIENT_ID} client...")
    client = await get_client(admin_token)
    if not client:
        print(f"[ERROR] Client '{CLIENT_ID}' not found")
        sys.exit(1)
    
    print(f"[OK] Found client (UUID: {client.get('id')})")
    print()
    
    # Check current post-logout URIs
    current_logout_uris = client.get("attributes", {}).get("post.logout.redirect.uris", "")
    print(f"Current post-logout redirect URIs: {current_logout_uris}")
    print()
    
    # Update client
    print("Updating client configuration...")
    success = await update_client(admin_token, client.get('id'))
    
    if success:
        print()
        print("=" * 70)
        print("[OK] Configuration updated successfully!")
        print("=" * 70)
        print()
        print("The logout should now redirect to:")
        print(f"  {FRONTEND_URL}/login")
        print()
        print("Note: If logout still doesn't work, try:")
        print("  1. Clear browser cache and cookies")
        print("  2. Log out and log back in")
        print("  3. Check browser console for any errors")
    else:
        print()
        print("=" * 70)
        print("[ERROR] Failed to update configuration")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

