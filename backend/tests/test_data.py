# tests/test_data.py

import asyncio
import httpx
from datetime import datetime, timedelta, timezone
from app.config import settings

BASE_URL = "http://localhost:8000/api"
KEYCLOAK_URL = "http://localhost:8080"

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "adminsecure123"
REALM = "master"  # Updated to match current Keycloak configuration
CLIENT_ID = "admin-frontend"  # Use frontend client for testing
CLIENT_SECRET = None  # Public client, no secret needed

async def get_keycloak_token():
    """Get JWT token from Keycloak"""
    print("🔐 Getting authentication token from Keycloak...")
    
    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    
    data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(token_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                print(f"✅ Successfully obtained token")
                return access_token
            else:
                print(f"❌ Failed to get token: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error getting token: {str(e)}")
            return None

async def create_test_user_in_db(token):
    """Sync Keycloak user to database"""
    print("\n👤 Creating user in database...")
    
    async with httpx.AsyncClient() as client:
        try:
            # First, try to get current user (this will create user in DB if not exists)
            response = await client.get(
                f"{BASE_URL}/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                user = response.json()
                print(f"✅ User exists/created: {user.get('username')}")
                return user
            else:
                print(f"❌ Failed to get/create user: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

async def create_enrollment_code(token):
    """Create enrollment code"""
    print("\n1️⃣ Creating enrollment code...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/enrollment/codes",
                json={
                    "description": "Test enrollment code",
                    "max_uses": 5,
                    "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 201:
                enrollment_code = response.json()
                print(f"✅ Created enrollment code: {enrollment_code['code']}")
                return enrollment_code
            else:
                print(f"❌ Failed to create enrollment code: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

async def enroll_device(token, enrollment_code):
    """Enroll a test device"""
    print("\n2️⃣ Enrolling test device...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/devices/enroll",
                json={
                    "enrollment_code": enrollment_code,
                    "device_name": "Test Laptop",
                    "device_unique_id": f"test-tpm-{datetime.now().timestamp()}",
                    "tpm_public_key": "-----BEGIN PUBLIC KEY-----\nTEST_KEY\n-----END PUBLIC KEY-----",
                    "os_type": "Windows",
                    "os_version": "11",
                    "device_model": "ThinkPad X1",
                    "manufacturer": "Lenovo"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 201:
                device = response.json()
                print(f"✅ Enrolled device: {device['device_name']} (ID: {device['id']})")
                return device
            else:
                print(f"❌ Failed to enroll device: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

async def submit_posture(token, device_unique_id):
    """Submit posture data"""
    print("\n3️⃣ Submitting posture data...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/posture/submit",
                json={
                    "device_unique_id": device_unique_id,
                    "posture_data": {
                        "antivirus_enabled": True,
                        "firewall_enabled": True,
                        "disk_encrypted": True,
                        "pending_updates": 5,
                        "screen_lock_enabled": True
                    },
                    "signature": "test_signature"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 201:
                posture = response.json()
                print(f"✅ Posture submitted: Compliant={posture['is_compliant']}, Score={posture['compliance_score']}")
                return posture
            else:
                print(f"❌ Failed to submit posture: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

async def create_policy(token):
    """Create a test policy"""
    print("\n4️⃣ Creating test policy...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/policies/",
                json={
                    "name": "Default Posture Policy",
                    "description": "Requires antivirus, firewall, and disk encryption",
                    "policy_type": "posture",
                    "rules": {
                        "antivirus_enabled": True,
                        "firewall_enabled": True,
                        "disk_encrypted": True,
                        "min_os_version": "10.0",
                        "max_pending_updates": 10
                    },
                    "priority": 100,
                    "enforce_mode": "enforce"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 201:
                policy = response.json()
                print(f"✅ Created policy: {policy['name']} (ID: {policy['id']})")
                return policy
            else:
                print(f"❌ Failed to create policy: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

async def list_audit_logs(token):
    """Get audit logs"""
    print("\n5️⃣ Fetching audit logs...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/audit/logs/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                logs = response.json()
                print(f"✅ Found {len(logs)} audit log entries")
                for log in logs[:3]:  # Show first 3
                    print(f"   - {log['event_type']}: {log['action']} ({log['status']})")
                return logs
            else:
                print(f"❌ Failed to get audit logs: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

async def run_all_tests():
    """Run all tests in sequence"""
    print("🧪 Starting ZTNA Backend Integration Tests...\n")
    print("="*60)
    
    # 1. Get authentication token
    token = await get_keycloak_token()
    if not token:
        print("\n❌ Cannot proceed without authentication token")
        return
    
    # 2. Create/verify user
    user = await create_test_user_in_db(token)
    if not user:
        print("\n❌ Cannot proceed without user")
        return
    
    # 3. Create enrollment code
    enrollment = await create_enrollment_code(token)
    if not enrollment:
        print("\n⚠️  Skipping device enrollment (no code)")
    else:
        # 4. Enroll device
        device = await enroll_device(token, enrollment['code'])
        if device:
            # 5. Submit posture
            await submit_posture(token, device['device_unique_id'])
    
    # 6. Create policy
    await create_policy(token)
    
    # 7. List audit logs
    await list_audit_logs(token)
    
    print("\n" + "="*60)
    print("✅ Tests completed!\n")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
