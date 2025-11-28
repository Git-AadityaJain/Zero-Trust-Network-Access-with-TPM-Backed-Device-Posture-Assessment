#!/usr/bin/env python3
"""
Script to update Keycloak admin-frontend client post-logout redirect URIs
This script will:
1. Get admin token
2. Find admin-frontend client
3. Update post.logout.redirect.uris attribute
4. Verify the update
"""

import asyncio
import sys
import os
import httpx
import json
import re

# Configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "https://unimplied-untranscendental-denita.ngrok-free.dev/auth")
REALM = "master"
CLIENT_ID = "admin-frontend"
ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "adminsecure123")

# Post-logout redirect URIs to configure
# This will be dynamically determined from KEYCLOAK_URL
# Localhost and other non-ngrok URLs are preserved

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
                print(f"[ERROR] Failed to get admin token: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"[ERROR] Error getting admin token: {e}")
            return None

async def get_client(admin_token):
    """Get client by clientId"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params={"clientId": CLIENT_ID}, timeout=10.0)
            if response.status_code == 200:
                clients = response.json()
                return clients[0] if clients else None
            else:
                print(f"[ERROR] Failed to get client: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"[ERROR] Error getting client: {e}")
            return None

def is_ngrok_url(url):
    """Check if URL is an ngrok URL"""
    return bool(re.match(r'https?://[^/]+\.ngrok(-free)?\.(app|dev|io)', url))

async def update_client_config(admin_token, client_uuid, frontend_url):
    """Update client configuration: redirect URIs, web origins, and post-logout redirect URIs"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_uuid}"
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    # Get current client configuration
    async with httpx.AsyncClient() as client:
        try:
            # First, get the current client config
            get_response = await client.get(url, headers=headers, timeout=10.0)
            if get_response.status_code != 200:
                print(f"[ERROR] Failed to get current client config: {get_response.status_code}")
                return False
            
            current_config = get_response.json()
            changes_made = False
            
            # Update redirect URIs - remove old ngrok URLs, add new one
            if "redirectUris" not in current_config:
                current_config["redirectUris"] = []
            
            # Filter out old ngrok URLs, keep localhost and other non-ngrok URLs
            filtered_redirect_uris = [uri for uri in current_config["redirectUris"] if not is_ngrok_url(uri)]
            new_callback_uri = f"{frontend_url}/callback"
            if new_callback_uri not in filtered_redirect_uris:
                filtered_redirect_uris.append(new_callback_uri)
                changes_made = True
            
            removed_redirect = len(current_config["redirectUris"]) - len([u for u in current_config["redirectUris"] if not is_ngrok_url(u)])
            if removed_redirect > 0:
                changes_made = True
                print(f"   Removed {removed_redirect} old ngrok redirect URI(s)")
            
            current_config["redirectUris"] = filtered_redirect_uris
            
            # Update web origins - remove old ngrok URLs, add new one
            if "webOrigins" not in current_config:
                current_config["webOrigins"] = []
            
            # Filter out old ngrok URLs, keep localhost and other non-ngrok URLs
            filtered_web_origins = [origin for origin in current_config["webOrigins"] if not is_ngrok_url(origin)]
            if frontend_url not in filtered_web_origins:
                filtered_web_origins.append(frontend_url)
                changes_made = True
            
            removed_web_origins = len(current_config["webOrigins"]) - len([o for o in current_config["webOrigins"] if not is_ngrok_url(o)])
            if removed_web_origins > 0:
                changes_made = True
                print(f"   Removed {removed_web_origins} old ngrok web origin(s)")
            
            current_config["webOrigins"] = filtered_web_origins
            
            # Update post-logout redirect URIs - remove old ngrok URLs, add new one
            if "attributes" not in current_config:
                current_config["attributes"] = {}
            
            current_logout_uris = current_config["attributes"].get("post.logout.redirect.uris", "")
            if current_logout_uris:
                logout_uri_list = [uri.strip() for uri in current_logout_uris.split(",") if uri.strip()]
            else:
                logout_uri_list = []
            
            # Filter out old ngrok URLs, keep localhost and other non-ngrok URLs
            filtered_logout_uris = [uri for uri in logout_uri_list if not is_ngrok_url(uri)]
            new_logout_uri = f"{frontend_url}/login"
            if new_logout_uri not in filtered_logout_uris:
                filtered_logout_uris.append(new_logout_uri)
                changes_made = True
            
            removed_logout = len(logout_uri_list) - len([u for u in logout_uri_list if not is_ngrok_url(u)])
            if removed_logout > 0:
                changes_made = True
                print(f"   Removed {removed_logout} old ngrok post-logout redirect URI(s)")
            
            current_config["attributes"]["post.logout.redirect.uris"] = ",".join(filtered_logout_uris)
            
            # Only update if changes were made
            if changes_made:
                # Update the client
                update_response = await client.put(url, headers=headers, json=current_config, timeout=10.0)
                if update_response.status_code == 204:
                    return True
                else:
                    print(f"[ERROR] Failed to update client: {update_response.status_code}")
                    print(f"   Response: {update_response.text}")
                    return False
            else:
                print("   No changes needed - configuration is already up to date")
                return True
        except Exception as e:
            print(f"[ERROR] Error updating client: {e}")
            return False

async def verify_logout_uris(admin_token, client_uuid):
    """Verify post-logout redirect URIs are configured correctly"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_uuid}"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                config = response.json()
                logout_uris = config.get("attributes", {}).get("post.logout.redirect.uris", "")
                return logout_uris
            else:
                return None
        except Exception as e:
            print(f"[ERROR] Error verifying configuration: {e}")
            return None

async def main():
    """Main function"""
    print("=" * 70)
    print("Keycloak Client Configuration Update Script")
    print("=" * 70)
    print(f"\nKeycloak URL: {KEYCLOAK_URL}")
    print(f"Realm: {REALM}")
    print(f"Client ID: {CLIENT_ID}")
    
    # Extract frontend URL from Keycloak URL (remove /auth if present)
    if KEYCLOAK_URL.endswith('/auth'):
        frontend_url = KEYCLOAK_URL[:-5]  # Remove '/auth'
    else:
        # Try to extract from URL structure
        frontend_url = KEYCLOAK_URL.replace('/auth', '')
    
    print(f"Frontend URL: {frontend_url}")
    print(f"\nThis script will:")
    print(f"  - Remove old ngrok URLs from redirect URIs, web origins, and post-logout URIs")
    print(f"  - Add new redirect URI: {frontend_url}/callback")
    print(f"  - Add new web origin: {frontend_url}")
    print(f"  - Add new post-logout URI: {frontend_url}/login")
    print(f"  - Preserve localhost and other non-ngrok URLs")
    print()
    
    # Get admin token
    print("Getting admin token...")
    admin_token = await get_admin_token()
    if not admin_token:
        print("[ERROR] Failed to get admin token. Please check:")
        print("   - KEYCLOAK_URL environment variable")
        print("   - KEYCLOAK_ADMIN_USER and KEYCLOAK_ADMIN_PASSWORD")
        sys.exit(1)
    print("[OK] Admin token obtained")
    
    # Get client
    print(f"\nFinding client '{CLIENT_ID}'...")
    client = await get_client(admin_token)
    if not client:
        print(f"[ERROR] Client '{CLIENT_ID}' not found")
        sys.exit(1)
    
    client_uuid = client["id"]
    client_name = client.get("name", CLIENT_ID)
    print(f"[OK] Found client: {client_name} (UUID: {client_uuid})")
    
    # Check current configuration
    print("\nChecking current configuration...")
    current_uris = client.get("attributes", {}).get("post.logout.redirect.uris", "")
    if current_uris:
        print(f"   Current post-logout URIs: {current_uris}")
        current_list = [uri.strip() for uri in current_uris.split(",") if uri.strip()]
        print(f"   Current count: {len(current_list)}")
    else:
        print("   No post-logout URIs currently configured")
    
    # Update configuration
    print(f"\nUpdating client configuration...")
    success = await update_client_config(admin_token, client_uuid, frontend_url)
    if not success:
        print("[ERROR] Failed to update client configuration")
        sys.exit(1)
    print("[OK] Client configuration updated")
    
    # Verify update
    print("\nVerifying update...")
    await asyncio.sleep(1)  # Give Keycloak a moment to process
    
    # Get updated client config
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_uuid}"
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                config = response.json()
                
                # Check redirect URIs
                redirect_uris = config.get("redirectUris", [])
                print(f"   Redirect URIs ({len(redirect_uris)}): {', '.join(redirect_uris[:3])}{'...' if len(redirect_uris) > 3 else ''}")
                
                # Check web origins
                web_origins = config.get("webOrigins", [])
                print(f"   Web Origins ({len(web_origins)}): {', '.join(web_origins[:3])}{'...' if len(web_origins) > 3 else ''}")
                
                # Check post-logout URIs
                logout_uris = config.get("attributes", {}).get("post.logout.redirect.uris", "")
                if logout_uris:
                    logout_list = [uri.strip() for uri in logout_uris.split(",") if uri.strip()]
                    print(f"   Post-Logout URIs ({len(logout_list)}): {', '.join(logout_list[:3])}{'...' if len(logout_list) > 3 else ''}")
                    
                    # Verify new logout URI is present
                    expected_logout = f"{frontend_url}/login"
                    if expected_logout in logout_list:
                        print(f"\n[OK] Verified: New post-logout URI is configured: {expected_logout}")
                    else:
                        print(f"\n[WARNING] Expected post-logout URI not found: {expected_logout}")
                else:
                    print("   [WARNING] No post-logout redirect URIs configured")
            else:
                print("[WARNING] Could not verify configuration (but update may have succeeded)")
        except Exception as e:
            print(f"[WARNING] Could not verify configuration: {e}")
    
    print("\n" + "=" * 70)
    print("[OK] Configuration update complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Test logout functionality")
    print("2. Verify redirect to /login works correctly")
    print("3. Check Keycloak logs for any errors")
    print()

if __name__ == "__main__":
    asyncio.run(main())

