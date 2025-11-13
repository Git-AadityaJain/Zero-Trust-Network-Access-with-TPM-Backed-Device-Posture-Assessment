# tests/test_all_endpoints_complete.py

"""
ZTNA Backend - Complete API Endpoint Testing
Includes DELETE operations with dedicated deletable test resources
All operations are tracked in audit logs
"""

import asyncio
import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.config import settings

BASE_URL = "http://localhost:8000/api"
KEYCLOAK_URL = "http://localhost:8080"

# Configuration
REALM = "ZTNA-Platform"
CLIENT_ID = "ztna-backend"
CLIENT_SECRET = settings.OIDC_CLIENT_SECRET  # Replace with actual secret
TEST_USERNAME = "admin-user"
TEST_PASSWORD = "Test123!"

# Store test data
test_data = {
    "token": None,
    "user": None,
    "enrollment_code": None,
    "device": None,
    "policy": None,
    # Deletable resources (created specifically for deletion)
    "deletable_device": None,
    "deletable_policy": None,
    "deletable_enrollment_code": None
}

# Test statistics
stats = {
    "passed": 0,
    "failed": 0,
    "total": 0
}

def log_result(test_name: str, passed: bool):
    """Log test result"""
    stats["total"] += 1
    if passed:
        stats["passed"] += 1
    else:
        stats["failed"] += 1

async def get_token():
    """Get authentication token"""
    print("\n🔐 Getting authentication token...")
    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    
    data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        if response.status_code == 200:
            token = response.json().get("access_token")
            test_data["token"] = token
            print(f"✅ Token obtained")
            return token
        else:
            print(f"❌ Failed to get token: {response.status_code}")
            return None

def get_headers():
    """Get authorization headers"""
    return {"Authorization": f"Bearer {test_data['token']}"}

# ==============================================
# USER ENDPOINT TESTS
# ==============================================

async def test_get_current_user():
    """Test GET /api/users/me"""
    print("\n👤 Testing GET /api/users/me")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/users/me", headers=get_headers())
        if response.status_code == 200:
            user = response.json()
            test_data["user"] = user
            print(f"✅ User: {user['username']} ({user['email']})")
            log_result("GET /api/users/me", True)
            return user
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("GET /api/users/me", False)
            return None

async def test_get_current_user_with_devices():
    """Test GET /api/users/me/devices"""
    print("\n👤 Testing GET /api/users/me/devices")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/users/me/devices", headers=get_headers())
        if response.status_code == 200:
            user = response.json()
            print(f"✅ User has {len(user.get('devices', []))} device(s)")
            log_result("GET /api/users/me/devices", True)
            return user
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("GET /api/users/me/devices", False)
            return None

async def test_update_user():
    """Test PATCH /api/users/me"""
    print("\n👤 Testing PATCH /api/users/me")
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/users/me",
            json={"first_name": "Test", "last_name": "User"},
            headers=get_headers()
        )
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Updated user: {user['first_name']} {user['last_name']}")
            log_result("PATCH /api/users/me", True)
            return user
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("PATCH /api/users/me", False)
            return None

# ==============================================
# ENROLLMENT ENDPOINT TESTS
# ==============================================

async def test_create_enrollment_code():
    """Test POST /api/enrollment/codes/"""
    print("\n🎫 Testing POST /api/enrollment/codes/ (permanent)")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/enrollment/codes",
            json={
                "description": "Permanent test enrollment code",
                "max_uses": 10,
                "expires_at": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
            },
            headers=get_headers()
        )
        if response.status_code == 201:
            code = response.json()
            test_data["enrollment_code"] = code
            print(f"✅ Created code: {code['code']}")
            log_result("POST /api/enrollment/codes/", True)
            return code
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            log_result("POST /api/enrollment/codes/", False)
            return None

async def test_create_deletable_enrollment_code():
    """Test POST /api/enrollment/codes/ (for deletion)"""
    print("\n🎫 Testing POST /api/enrollment/codes/ (deletable)")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/enrollment/codes",
            json={
                "description": "⚠️ DELETABLE - Test enrollment code for deletion",
                "max_uses": 1,
                "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            },
            headers=get_headers()
        )
        if response.status_code == 201:
            code = response.json()
            test_data["deletable_enrollment_code"] = code
            print(f"✅ Created deletable code: {code['code']}")
            log_result("POST /api/enrollment/codes/ (deletable)", True)
            return code
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            log_result("POST /api/enrollment/codes/ (deletable)", False)
            return None

async def test_list_enrollment_codes():
    """Test GET /api/enrollment/codes"""
    print("\n🎫 Testing GET /api/enrollment/codes")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/enrollment/codes", headers=get_headers())
        if response.status_code == 200:
            codes = response.json()
            print(f"✅ Found {len(codes)} enrollment code(s)")
            log_result("GET /api/enrollment/codes", True)
            return codes
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("GET /api/enrollment/codes", False)
            return None

async def test_deactivate_enrollment_code():
    """Test POST /api/enrollment/codes/{id}/deactivate"""
    if not test_data.get("deletable_enrollment_code"):
        print("\n⏭️  Skipping deactivate test (no deletable code)")
        return None
    
    code_id = test_data["deletable_enrollment_code"]["id"]
    print(f"\n🎫 Testing POST /api/enrollment/codes/{code_id}/deactivate")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/enrollment/codes/{code_id}/deactivate",
            headers=get_headers()
        )
        if response.status_code == 200:
            code = response.json()
            print(f"✅ Deactivated code (active: {code['is_active']})")
            log_result("POST /api/enrollment/codes/{id}/deactivate", True)
            return code
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("POST /api/enrollment/codes/{id}/deactivate", False)
            return None

# ==============================================
# DEVICE ENDPOINT TESTS
# ==============================================

async def test_enroll_device():
    """Test POST /api/devices/enroll (permanent)"""
    if not test_data.get("enrollment_code"):
        await test_create_enrollment_code()
    
    print("\n💻 Testing POST /api/devices/enroll (permanent)")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/devices/enroll",
            json={
                "enrollment_code": test_data["enrollment_code"]["code"],
                "device_name": "Permanent Test Device",
                "device_unique_id": f"permanent-tpm-{int(datetime.now().timestamp())}",
                "tpm_public_key": "-----BEGIN PUBLIC KEY-----\nPERMANENT_KEY\n-----END PUBLIC KEY-----",
                "os_type": "Windows",
                "os_version": "11",
                "device_model": "Surface Laptop",
                "manufacturer": "Microsoft"
            },
            headers=get_headers()
        )
        if response.status_code == 201:
            device = response.json()
            test_data["device"] = device
            print(f"✅ Enrolled device: {device['device_name']} (ID: {device['id']})")
            log_result("POST /api/devices/enroll", True)
            return device
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            log_result("POST /api/devices/enroll", False)
            return None

async def test_enroll_deletable_device():
    """Test POST /api/devices/enroll (for deletion)"""
    if not test_data.get("enrollment_code"):
        await test_create_enrollment_code()
    
    print("\n💻 Testing POST /api/devices/enroll (deletable)")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/devices/enroll",
            json={
                "enrollment_code": test_data["enrollment_code"]["code"],
                "device_name": "⚠️ DELETABLE - Test Device for Deletion",
                "device_unique_id": f"deletable-tpm-{int(datetime.now().timestamp())}",
                "tpm_public_key": "-----BEGIN PUBLIC KEY-----\nDELETABLE_KEY\n-----END PUBLIC KEY-----",
                "os_type": "Linux",
                "os_version": "Ubuntu 22.04",
                "device_model": "Test VM",
                "manufacturer": "VirtualBox"
            },
            headers=get_headers()
        )
        if response.status_code == 201:
            device = response.json()
            test_data["deletable_device"] = device
            print(f"✅ Enrolled deletable device: {device['device_name']} (ID: {device['id']})")
            log_result("POST /api/devices/enroll (deletable)", True)
            return device
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            log_result("POST /api/devices/enroll (deletable)", False)
            return None

async def test_list_devices():
    """Test GET /api/devices"""
    print("\n💻 Testing GET /api/devices")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/devices", headers=get_headers())
        if response.status_code == 200:
            devices = response.json()
            print(f"✅ Found {len(devices)} device(s)")
            for device in devices:
                marker = "⚠️ " if "DELETABLE" in device['device_name'] else ""
                print(f"   {marker}- {device['device_name']} (Compliant: {device['is_compliant']})")
            log_result("GET /api/devices", True)
            return devices
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("GET /api/devices", False)
            return None

async def test_get_device():
    """Test GET /api/devices/{id}"""
    if not test_data.get("device"):
        print("\n⏭️  Skipping get device test")
        return None
    
    device_id = test_data["device"]["id"]
    print(f"\n💻 Testing GET /api/devices/{device_id}")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/devices/{device_id}", headers=get_headers())
        if response.status_code == 200:
            device = response.json()
            print(f"✅ Device: {device['device_name']}")
            log_result("GET /api/devices/{id}", True)
            return device
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("GET /api/devices/{id}", False)
            return None

async def test_update_device():
    """Test PATCH /api/devices/{id}"""
    if not test_data.get("device"):
        print("\n⏭️  Skipping update device test")
        return None
    
    device_id = test_data["device"]["id"]
    print(f"\n💻 Testing PATCH /api/devices/{device_id}")
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/devices/{device_id}",
            json={"device_name": "Permanent Test Device (Updated)"},
            headers=get_headers()
        )
        if response.status_code == 200:
            device = response.json()
            print(f"✅ Updated device: {device['device_name']}")
            log_result("PATCH /api/devices/{id}", True)
            return device
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("PATCH /api/devices/{id}", False)
            return None

async def test_delete_device():
    """Test DELETE /api/devices/{id}"""
    if not test_data.get("deletable_device"):
        print("\n⏭️  Skipping delete device test")
        return None
    
    device_id = test_data["deletable_device"]["id"]
    device_name = test_data["deletable_device"]["device_name"]
    print(f"\n💻 Testing DELETE /api/devices/{device_id}")
    print(f"   Deleting: {device_name}")
    
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{BASE_URL}/devices/{device_id}",
            headers=get_headers()
        )
        if response.status_code == 204:
            print(f"✅ Device deleted successfully")
            print(f"   ℹ️  Check audit logs for deletion record")
            log_result("DELETE /api/devices/{id}", True)
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("DELETE /api/devices/{id}", False)
            return False

# ==============================================
# POSTURE ENDPOINT TESTS
# ==============================================

async def test_submit_posture():
    """Test POST /api/posture/submit"""
    if not test_data.get("device"):
        print("\n⏭️  Skipping posture submit test")
        return None
    
    print("\n🛡️  Testing POST /api/posture/submit")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/posture/submit",
            json={
                "device_unique_id": test_data["device"]["device_unique_id"],
                "posture_data": {
                    "antivirus_enabled": True,
                    "firewall_enabled": True,
                    "disk_encrypted": True,
                    "pending_updates": 3,
                    "screen_lock_enabled": True
                },
                "signature": "test_signature_123"
            },
            headers=get_headers()
        )
        if response.status_code == 201:
            posture = response.json()
            print(f"✅ Posture: Compliant={posture['is_compliant']}, Score={posture['compliance_score']}")
            if posture.get('violations'):
                print(f"   Violations: {posture['violations']}")
            log_result("POST /api/posture/submit", True)
            return posture
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            log_result("POST /api/posture/submit", False)
            return None

async def test_get_posture_history():
    """Test GET /api/posture/device/{id}/history"""
    if not test_data.get("device"):
        print("\n⏭️  Skipping posture history test")
        return None
    
    device_id = test_data["device"]["id"]
    print(f"\n🛡️  Testing GET /api/posture/device/{device_id}/history")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/posture/device/{device_id}/history",
            headers=get_headers()
        )
        if response.status_code == 200:
            history = response.json()
            print(f"✅ Found {len(history)} posture check(s)")
            log_result("GET /api/posture/device/{id}/history", True)
            return history
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("GET /api/posture/device/{id}/history", False)
            return None

async def test_get_latest_posture():
    """Test GET /api/posture/device/{id}/latest"""
    if not test_data.get("device"):
        print("\n⏭️  Skipping latest posture test")
        return None
    
    device_id = test_data["device"]["id"]
    print(f"\n🛡️  Testing GET /api/posture/device/{device_id}/latest")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/posture/device/{device_id}/latest",
            headers=get_headers()
        )
        if response.status_code == 200:
            posture = response.json()
            print(f"✅ Latest posture: Compliant={posture['is_compliant']}, Score={posture['compliance_score']}")
            log_result("GET /api/posture/device/{id}/latest", True)
            return posture
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("GET /api/posture/device/{id}/latest", False)
            return None

# ==============================================
# POLICY ENDPOINT TESTS
# ==============================================

async def test_create_policy():
    """Test POST /api/policies/ (permanent)"""
    print("\n📋 Testing POST /api/policies/ (permanent)")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/policies/",
            json={
                "name": "Permanent Security Policy",
                "description": "Comprehensive security policy for production",
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
            headers=get_headers()
        )
        if response.status_code == 201:
            policy = response.json()
            test_data["policy"] = policy
            print(f"✅ Created policy: {policy['name']} (ID: {policy['id']})")
            log_result("POST /api/policies/", True)
            return policy
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            log_result("POST /api/policies/", False)
            return None

async def test_create_deletable_policy():
    """Test POST /api/policies/ (for deletion)"""
    print("\n📋 Testing POST /api/policies/ (deletable)")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/policies/",
            json={
                "name": f"⚠️ DELETABLE Policy {datetime.now().timestamp()}",
                "description": "Temporary policy for deletion testing",
                "policy_type": "posture",
                "rules": {
                    "antivirus_enabled": True,
                    "firewall_enabled": False
                },
                "priority": 50,
                "enforce_mode": "monitor"
            },
            headers=get_headers()
        )
        if response.status_code == 201:
            policy = response.json()
            test_data["deletable_policy"] = policy
            print(f"✅ Created deletable policy: {policy['name']} (ID: {policy['id']})")
            log_result("POST /api/policies/ (deletable)", True)
            return policy
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            log_result("POST /api/policies/ (deletable)", False)
            return None

async def test_list_policies():
    """Test GET /api/policies"""
    print("\n📋 Testing GET /api/policies")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/policies", headers=get_headers())
        if response.status_code == 200:
            policies = response.json()
            print(f"✅ Found {len(policies)} policy/policies")
            for policy in policies:
                marker = "⚠️ " if "DELETABLE" in policy['name'] else ""
                print(f"   {marker}- {policy['name']} (Active: {policy['is_active']})")
            log_result("GET /api/policies", True)
            return policies
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("GET /api/policies", False)
            return None

async def test_get_policy():
    """Test GET /api/policies/{id}"""
    if not test_data.get("policy"):
        print("\n⏭️  Skipping get policy test")
        return None
    
    policy_id = test_data["policy"]["id"]
    print(f"\n📋 Testing GET /api/policies/{policy_id}")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/policies/{policy_id}", headers=get_headers())
        if response.status_code == 200:
            policy = response.json()
            print(f"✅ Policy: {policy['name']}")
            log_result("GET /api/policies/{id}", True)
            return policy
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("GET /api/policies/{id}", False)
            return None

async def test_update_policy():
    """Test PATCH /api/policies/{id}"""
    if not test_data.get("policy"):
        print("\n⏭️  Skipping update policy test")
        return None
    
    policy_id = test_data["policy"]["id"]
    print(f"\n📋 Testing PATCH /api/policies/{policy_id}")
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/policies/{policy_id}",
            json={"priority": 150, "description": "Updated policy description"},
            headers=get_headers()
        )
        if response.status_code == 200:
            policy = response.json()
            print(f"✅ Updated policy: Priority={policy['priority']}")
            log_result("PATCH /api/policies/{id}", True)
            return policy
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("PATCH /api/policies/{id}", False)
            return None

async def test_deactivate_policy():
    """Test POST /api/policies/{id}/deactivate"""
    if not test_data.get("deletable_policy"):
        print("\n⏭️  Skipping deactivate policy test")
        return None
    
    policy_id = test_data["deletable_policy"]["id"]
    print(f"\n📋 Testing POST /api/policies/{policy_id}/deactivate")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/policies/{policy_id}/deactivate",
            headers=get_headers()
        )
        if response.status_code == 200:
            policy = response.json()
            print(f"✅ Deactivated policy (Active: {policy['is_active']})")
            log_result("POST /api/policies/{id}/deactivate", True)
            return policy
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("POST /api/policies/{id}/deactivate", False)
            return None

async def test_activate_policy():
    """Test POST /api/policies/{id}/activate"""
    if not test_data.get("deletable_policy"):
        print("\n⏭️  Skipping activate policy test")
        return None
    
    policy_id = test_data["deletable_policy"]["id"]
    print(f"\n📋 Testing POST /api/policies/{policy_id}/activate")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/policies/{policy_id}/activate",
            headers=get_headers()
        )
        if response.status_code == 200:
            policy = response.json()
            print(f"✅ Activated policy (Active: {policy['is_active']})")
            log_result("POST /api/policies/{id}/activate", True)
            return policy
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("POST /api/policies/{id}/activate", False)
            return None

async def test_delete_policy():
    """Test DELETE /api/policies/{id}"""
    if not test_data.get("deletable_policy"):
        print("\n⏭️  Skipping delete policy test")
        return None
    
    policy_id = test_data["deletable_policy"]["id"]
    policy_name = test_data["deletable_policy"]["name"]
    print(f"\n📋 Testing DELETE /api/policies/{policy_id}")
    print(f"   Deleting: {policy_name}")
    
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{BASE_URL}/policies/{policy_id}",
            headers=get_headers()
        )
        if response.status_code == 204:
            print(f"✅ Policy deleted successfully")
            print(f"   ℹ️  Check audit logs for deletion record")
            log_result("DELETE /api/policies/{id}", True)
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("DELETE /api/policies/{id}", False)
            return False

# ==============================================
# AUDIT ENDPOINT TESTS
# ==============================================

async def test_get_audit_logs():
    """Test GET /api/audit/logs"""
    print("\n📝 Testing GET /api/audit/logs")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/audit/logs?limit=20", headers=get_headers())
        if response.status_code == 200:
            logs = response.json()
            print(f"✅ Found {len(logs)} audit log(s)")
            
            # Show recent logs
            print("\n   Recent audit events:")
            for log in logs[:5]:
                emoji = "✅" if log['status'] == 'success' else "❌"
                print(f"   {emoji} {log['event_type']}: {log['action']} - {log.get('description', 'N/A')}")
            
            # Check for delete operations
            delete_logs = [log for log in logs if log['action'] == 'delete']
            if delete_logs:
                print(f"\n   🗑️  Found {len(delete_logs)} deletion record(s) in audit log:")
                for log in delete_logs:
                    print(f"      - {log['resource_type']} ID {log['resource_id']}: {log.get('description', 'N/A')}")
            
            log_result("GET /api/audit/logs", True)
            return logs
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("GET /api/audit/logs", False)
            return None

async def test_get_my_audit_logs():
    """Test GET /api/audit/logs/me"""
    print("\n📝 Testing GET /api/audit/logs/me")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/audit/logs/me?limit=20", headers=get_headers())
        if response.status_code == 200:
            logs = response.json()
            print(f"✅ Found {len(logs)} audit log(s) for current user")
            log_result("GET /api/audit/logs/me", True)
            return logs
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("GET /api/audit/logs/me", False)
            return None

async def test_get_event_types():
    """Test GET /api/audit/events/types"""
    print("\n📝 Testing GET /api/audit/events/types")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/audit/events/types", headers=get_headers())
        if response.status_code == 200:
            types = response.json()
            print(f"✅ Found {len(types)} event types")
            print(f"   Types: {', '.join(types)}")
            log_result("GET /api/audit/events/types", True)
            return types
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("GET /api/audit/events/types", False)
            return None

# ==============================================
# ACCESS ENDPOINT TESTS
# ==============================================

async def test_get_access_logs():
    """Test GET /api/access/logs"""
    print("\n🔐 Testing GET /api/access/logs")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/access/logs?limit=10", headers=get_headers())
        if response.status_code == 200:
            logs = response.json()
            print(f"✅ Found {len(logs)} access log(s)")
            log_result("GET /api/access/logs", True)
            return logs
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("GET /api/access/logs", False)
            return None

async def test_get_my_devices_access_logs():
    """Test GET /api/access/me/devices"""
    print("\n🔐 Testing GET /api/access/me/devices")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/access/me/devices", headers=get_headers())
        if response.status_code == 200:
            logs = response.json()
            print(f"✅ Found {len(logs)} access log(s) for my devices")
            log_result("GET /api/access/me/devices", True)
            return logs
        else:
            print(f"❌ Failed: {response.status_code}")
            log_result("GET /api/access/me/devices", False)
            return None

# ==============================================
# MAIN TEST RUNNER
# ==============================================

async def run_all_tests():
    """Run all endpoint tests including DELETE operations"""
    print("=" * 80)
    print("🧪 ZTNA Backend - COMPLETE API Endpoint Testing with DELETE Operations")
    print("=" * 80)
    
    # Get authentication token
    token = await get_token()
    if not token:
        print("\n❌ Cannot proceed without authentication token")
        return
    
    # USER TESTS
    print("\n" + "=" * 80)
    print("👤 USER ENDPOINTS")
    print("=" * 80)
    await test_get_current_user()
    await test_get_current_user_with_devices()
    await test_update_user()
    
    # ENROLLMENT TESTS
    print("\n" + "=" * 80)
    print("🎫 ENROLLMENT ENDPOINTS")
    print("=" * 80)
    await test_create_enrollment_code()
    await test_create_deletable_enrollment_code()
    await test_list_enrollment_codes()
    
    # DEVICE TESTS
    print("\n" + "=" * 80)
    print("💻 DEVICE ENDPOINTS")
    print("=" * 80)
    await test_enroll_device()
    await test_enroll_deletable_device()
    await test_list_devices()
    await test_get_device()
    await test_update_device()
    
    # POSTURE TESTS
    print("\n" + "=" * 80)
    print("🛡️  POSTURE ENDPOINTS")
    print("=" * 80)
    await test_submit_posture()
    await test_get_posture_history()
    await test_get_latest_posture()
    
    # POLICY TESTS
    print("\n" + "=" * 80)
    print("📋 POLICY ENDPOINTS")
    print("=" * 80)
    await test_create_policy()
    await test_create_deletable_policy()
    await test_list_policies()
    await test_get_policy()
    await test_update_policy()
    await test_deactivate_policy()
    await test_activate_policy()
    
    # DELETE OPERATIONS (separate section for visibility)
    print("\n" + "=" * 80)
    print("🗑️  DELETE OPERATIONS (Check Audit Logs!)")
    print("=" * 80)
    await test_delete_device()
    await test_delete_policy()
    await test_deactivate_enrollment_code()  # Soft delete
    
    # AUDIT TESTS (show delete records)
    print("\n" + "=" * 80)
    print("📝 AUDIT ENDPOINTS (Verify Delete Operations)")
    print("=" * 80)
    await test_get_audit_logs()
    await test_get_my_audit_logs()
    await test_get_event_types()
    
    # ACCESS TESTS
    print("\n" + "=" * 80)
    print("🔐 ACCESS ENDPOINTS")
    print("=" * 80)
    await test_get_access_logs()
    await test_get_my_devices_access_logs()
    
    # FINAL SUMMARY
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {stats['passed']}/{stats['total']}")
    print(f"❌ Failed: {stats['failed']}/{stats['total']}")
    success_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    print("\n" + "=" * 80)
    print("📋 DELETABLE RESOURCES CREATED:")
    print("=" * 80)
    if test_data.get("deletable_device"):
        print(f"⚠️  Deletable Device: {test_data['deletable_device']['device_name']} (DELETED)")
    if test_data.get("deletable_policy"):
        print(f"⚠️  Deletable Policy: {test_data['deletable_policy']['name']} (DELETED)")
    if test_data.get("deletable_enrollment_code"):
        print(f"⚠️  Deletable Code: {test_data['deletable_enrollment_code']['code']} (DEACTIVATED)")
    
    print("\n" + "=" * 80)
    print("ℹ️  Check database audit_logs table to verify delete operations were logged!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
