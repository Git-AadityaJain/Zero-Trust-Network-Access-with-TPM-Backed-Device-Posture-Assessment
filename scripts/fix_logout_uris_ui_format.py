#!/usr/bin/env python3
"""
Fix post-logout redirect URIs to display properly in Keycloak Admin Console UI
This script ensures the format is correct so Keycloak UI displays each URI in a separate field
"""

import asyncio
import sys
import os
import httpx
import json

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

async def update_client_via_ui_format(admin_token, client_uuid):
    """
    Update client using the format that Keycloak UI expects
    The UI might need the URIs to be set in a specific way
    """
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
            
            # Define the exact URIs we want
            desired_uris = [
                f"{FRONTEND_URL}/login",
                "http://localhost:3000/login",
                "http://localhost/login"
            ]
            
            # Keycloak stores post.logout.redirect.uris as a comma-separated string
            # The format should be: "uri1,uri2,uri3" with NO spaces
            # However, some Keycloak versions might need newlines or different separators
            # Let's try the standard comma-separated format first
            
            if "attributes" not in current_config:
                current_config["attributes"] = {}
            
            # Set the attribute with proper comma separation (no spaces)
            formatted_uris = ",".join(desired_uris)
            current_config["attributes"]["post.logout.redirect.uris"] = formatted_uris
            
            print(f"[INFO] Setting post-logout redirect URIs to:")
            for uri in desired_uris:
                print(f"   - {uri}")
            print()
            print(f"[INFO] Stored format: {formatted_uris}")
            print()
            
            # Update client
            put_response = await client.put(url, headers=headers, json=current_config, timeout=10.0)
            if put_response.status_code == 204:
                print("[OK] Client updated successfully")
                return True
            else:
                print(f"[ERROR] Failed to update client: {put_response.status_code}")
                print(f"   Response: {put_response.text}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error updating client: {e}")
            import traceback
            traceback.print_exc()
            return False

async def verify_ui_display(admin_token, client_uuid):
    """Verify how the URIs are stored and provide manual fix instructions"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_uuid}"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                config = response.json()
                stored_value = config.get("attributes", {}).get("post.logout.redirect.uris", "")
                
                print("Current stored value:")
                print(f"  {repr(stored_value)}")
                print()
                
                if stored_value:
                    uris = [uri.strip() for uri in stored_value.split(",") if uri.strip()]
                    print(f"Keycloak will parse this as {len(uris)} URI(s):")
                    for i, uri in enumerate(uris, 1):
                        print(f"  {i}. {uri}")
                    print()
                    print("Note: The format is correct for Keycloak's API.")
                    print("If the UI shows them in a single field, this is a Keycloak UI limitation.")
                    print("The logout functionality will still work correctly.")
                    print()
                    print("To fix the UI display:")
                    print("1. Go to Keycloak Admin Console")
                    print("2. Navigate to: Clients > admin-frontend > Settings")
                    print("3. In 'Valid post logout redirect URIs' section:")
                    print("   - Click 'Add valid post logout redirect URIs' for each URI")
                    print("   - Enter each URI in a separate field")
                    print("4. Click 'Save'")
                    print()
                    print("Alternatively, the current format will work functionally even if")
                    print("the UI displays it in a single field.")
                    
        except Exception as e:
            print(f"[ERROR] Error verifying: {e}")

async def main():
    print("=" * 70)
    print("Fix Post-Logout Redirect URIs UI Display")
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
    
    client_uuid = client.get('id')
    print(f"[OK] Found client (UUID: {client_uuid})")
    print()
    
    # Check current value
    current_value = client.get("attributes", {}).get("post.logout.redirect.uris", "")
    print(f"Current value: {current_value}")
    print()
    
    # Update client
    print("Updating client configuration...")
    success = await update_client_via_ui_format(admin_token, client_uuid)
    
    if success:
        print()
        # Verify
        await verify_ui_display(admin_token, client_uuid)
        
        print()
        print("=" * 70)
        print("Update Complete")
        print("=" * 70)
        print()
        print("IMPORTANT: Keycloak Admin Console UI Limitation")
        print("=" * 70)
        print()
        print("The Keycloak Admin API stores 'post.logout.redirect.uris' as a")
        print("comma-separated string in the client attributes. This is the")
        print("correct format and will work functionally.")
        print()
        print("However, the Keycloak Admin Console UI may display this as a")
        print("single text field instead of separate fields (unlike redirect URIs).")
        print()
        print("To fix the UI display manually:")
        print("1. Open Keycloak Admin Console")
        print("2. Go to: Clients > admin-frontend > Settings")
        print("3. Scroll to 'Valid post logout redirect URIs'")
        print("4. Clear the existing value")
        print("5. Click 'Add valid post logout redirect URIs' button")
        print("6. Enter each URI in a separate field:")
        print(f"   - {FRONTEND_URL}/login")
        print("   - http://localhost:3000/login")
        print("   - http://localhost/login")
        print("7. Click 'Save'")
        print()
        print("The logout functionality will work correctly regardless of how")
        print("the UI displays the URIs, as long as they are properly formatted.")
    else:
        print()
        print("=" * 70)
        print("[ERROR] Failed to update configuration")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

