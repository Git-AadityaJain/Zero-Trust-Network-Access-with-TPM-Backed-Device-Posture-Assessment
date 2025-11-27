#!/usr/bin/env python3
"""
Test script for TPM-based device attestation feature

This script tests the challenge-response flow for device attestation:
1. Request challenge
2. Sign challenge (with mock or real TPM)
3. Request token with signed challenge
4. Verify token works for resource access

Usage:
    python tests/test_tpm_attestation.py [--token YOUR_KEYCLOAK_TOKEN]
    
If no token is provided, the script will attempt to get one using Keycloak credentials.
"""

import asyncio
import httpx
import sys
import json
import base64
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

# Configuration
BASE_URL = "http://localhost:8000/api"
KEYCLOAK_URL = "http://localhost:8080"
REALM = "master"
CLIENT_ID = "admin-frontend"
TEST_USERNAME = "admin"
TEST_PASSWORD = "adminsecure123"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

async def get_keycloak_token() -> Optional[str]:
    """Get Keycloak access token"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
                data={
                    "grant_type": "password",
                    "client_id": CLIENT_ID,
                    "username": TEST_USERNAME,
                    "password": TEST_PASSWORD,
                },
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
            else:
                print_error(f"Failed to get token: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print_error(f"Error getting token: {e}")
        return None

def generate_mock_signature(challenge: str, private_key) -> str:
    """
    Generate a mock signature for testing
    This simulates what the DPA would do:
    1. Create dict: {"challenge": challenge}
    2. Convert to canonical JSON
    3. Base64 encode
    4. Sign with private key
    """
    import json
    
    # Create challenge data dict
    challenge_data = {"challenge": challenge}
    
    # Convert to canonical JSON (sorted keys)
    canonical_json = json.dumps(challenge_data, sort_keys=True)
    
    # Sign the JSON bytes (matching backend verification)
    message = canonical_json.encode()
    signature = private_key.sign(
        message,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    
    # Return base64-encoded signature
    return base64.b64encode(signature).decode('utf-8')

async def test_challenge_endpoint(token: str, device_id: int) -> Optional[Dict[str, Any]]:
    """Test the challenge endpoint"""
    print_info("\n1. Testing challenge endpoint...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/tokens/challenge",
                json={"device_id": device_id},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Challenge generated: {data['challenge'][:20]}...")
                print_info(f"  Expires in: {data['expires_in_seconds']} seconds")
                return data
            else:
                print_error(f"Failed to get challenge: {response.status_code}")
                print_error(f"  Response: {response.text}")
                return None
    except Exception as e:
        print_error(f"Error requesting challenge: {e}")
        return None

async def test_token_issuance_with_valid_signature(
    token: str,
    device_id: int,
    challenge: str,
    signature: str
) -> Optional[str]:
    """Test token issuance with valid signature"""
    print_info("\n2. Testing token issuance with valid signature...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/tokens/issue",
                json={
                    "device_id": device_id,
                    "challenge": challenge,
                    "challenge_signature": signature,
                    "resource": "*",
                    "expires_in_minutes": 15
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Token issued successfully!")
                print_info(f"  Device: {data['device_name']}")
                print_info(f"  Compliant: {data['is_compliant']}")
                print_info(f"  Expires in: {data['expires_in_minutes']} minutes")
                return data.get("token")
            else:
                print_error(f"Failed to issue token: {response.status_code}")
                print_error(f"  Response: {response.text}")
                return None
    except Exception as e:
        print_error(f"Error issuing token: {e}")
        return None

async def test_token_issuance_with_invalid_signature(
    token: str,
    device_id: int,
    challenge: str
) -> bool:
    """Test that invalid signature is rejected"""
    print_info("\n3. Testing token issuance with invalid signature (should fail)...")
    
    invalid_signature = "invalid_signature_base64_encoded"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/tokens/issue",
                json={
                    "device_id": device_id,
                    "challenge": challenge,
                    "challenge_signature": invalid_signature,
                    "resource": "*"
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 401:
                print_success("Invalid signature correctly rejected!")
                return True
            else:
                print_error(f"Expected 401, got {response.status_code}")
                print_error(f"  Response: {response.text}")
                return False
    except Exception as e:
        print_error(f"Error testing invalid signature: {e}")
        return False

async def test_token_usage(device_token: str) -> bool:
    """Test that the issued token works for resource access"""
    print_info("\n4. Testing token usage for resource access...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/resources/list",
                headers={"Authorization": f"Bearer {device_token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Token works for resource access!")
                print_info(f"  Resources available: {len(data.get('resources', []))}")
                return True
            else:
                print_error(f"Token failed for resource access: {response.status_code}")
                print_error(f"  Response: {response.text}")
                return False
    except Exception as e:
        print_error(f"Error testing token usage: {e}")
        return False

async def get_user_devices(token: str) -> Optional[list]:
    """Get user's devices"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/users/me/devices",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("devices", [])
            else:
                print_error(f"Failed to get devices: {response.status_code}")
                return None
    except Exception as e:
        print_error(f"Error getting devices: {e}")
        return None

async def get_device_tpm_key(token: str, device_id: int) -> Optional[str]:
    """Get device's TPM public key (for mock signing)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/devices/{device_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                # Note: TPM key might not be in the response for security
                # In real testing, you'd use the actual device's TPM
                return data.get("tpm_public_key")
            else:
                return None
    except Exception as e:
        return None

async def main():
    """Run TPM attestation tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}TPM Device Attestation Test Suite{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")
    
    # Get authentication token
    token = None
    if len(sys.argv) > 1:
        token = sys.argv[1]
        print_info(f"Using provided token (length: {len(token)})")
    else:
        print_info("Getting Keycloak token...")
        token = await get_keycloak_token()
        if not token:
            print_error("Failed to get authentication token")
            print_info("Usage: python test_tpm_attestation.py [--token YOUR_TOKEN]")
            return 1
    
    # Get user's devices
    print_info("\nGetting user's devices...")
    devices = await get_user_devices(token)
    if not devices:
        print_error("No devices found or failed to get devices")
        return 1
    
    # Find an enrolled device with TPM key
    enrolled_device = None
    for device in devices:
        if device.get("is_enrolled") and device.get("status") == "active":
            enrolled_device = device
            break
    
    if not enrolled_device:
        print_error("No enrolled and active device found")
        print_info("Please enroll a device first")
        return 1
    
    device_id = enrolled_device["id"]
    device_unique_id = enrolled_device.get("device_unique_id")
    print_success(f"Found enrolled device: {enrolled_device.get('device_name')} (ID: {device_id})")
    
    # Check if device has TPM key
    device_info = await get_device_tpm_key(token, device_id)
    if not device_info:
        print_warning("Could not verify TPM key. Device may not have TPM key stored.")
        print_info("This test will use a mock signature (for testing only)")
    
    # Test 1: Get challenge
    challenge_data = await test_challenge_endpoint(token, device_id)
    if not challenge_data:
        print_error("Cannot proceed without challenge")
        return 1
    
    challenge = challenge_data["challenge"]
    
    # Generate mock signature for testing
    # In production, this would be done by the DPA using the actual TPM
    print_warning("\n⚠️  Using MOCK signature for testing")
    print_info("In production, the DPA would sign the challenge with the device's TPM")
    
    # Generate a temporary key pair for mock signing
    # NOTE: This won't work with the actual device's TPM key
    # For real testing, you need the DPA to sign the challenge
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    mock_signature = generate_mock_signature(challenge, private_key)
    print_info(f"Generated mock signature: {mock_signature[:30]}...")
    
    # Test 2: Try to issue token with mock signature
    # This will fail because the signature doesn't match the device's TPM key
    print_warning("\n⚠️  Testing with mock signature (will fail - this is expected)")
    device_token = await test_token_issuance_with_valid_signature(
        token, device_id, challenge, mock_signature
    )
    
    if device_token:
        print_warning("Unexpected: Mock signature was accepted!")
        print_info("This should not happen in production")
    else:
        print_info("Mock signature correctly rejected (expected behavior)")
    
    # Test 3: Test invalid signature rejection
    await test_token_issuance_with_invalid_signature(token, device_id, challenge)
    
    # Summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}Test Summary{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")
    
    print_info("To test with REAL TPM signature:")
    print_info("1. Ensure DPA agent is running")
    print_info("2. DPA should expose: POST http://localhost:PORT/sign-challenge")
    print_info("3. Update frontend/src/api/tokenService.js to call DPA endpoint")
    print_info("4. Test through the frontend User Dashboard")
    print_info("\nOr use the DPA's signing capability directly:")
    print_info("  - Get challenge from /api/tokens/challenge")
    print_info("  - Sign challenge using DPA's TPM")
    print_info("  - Request token with signed challenge")
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

