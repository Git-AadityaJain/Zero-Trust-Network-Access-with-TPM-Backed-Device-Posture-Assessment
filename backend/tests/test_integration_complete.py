#!/usr/bin/env python3
"""
Comprehensive Integration Test Script for ZTNA Platform
Tests all major components and integrations
"""

import requests
import json
import sys
from typing import Optional, Dict, Any

BASE_URL = "http://localhost/api"
KEYCLOAK_URL = "http://localhost:8080"
KEYCLOAK_REALM = "master"
KEYCLOAK_CLIENT_ID = "admin-frontend"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def test_health_check():
    """Test backend health endpoint"""
    print_info("Testing backend health check...")
    try:
        response = requests.get(f"{BASE_URL.replace('/api', '')}/health", timeout=5)
        if response.status_code == 200:
            print_success("Backend health check passed")
            return True
        else:
            print_error(f"Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Backend health check failed: {e}")
        return False

def test_keycloak_health():
    """Test Keycloak accessibility"""
    print_info("Testing Keycloak health...")
    try:
        response = requests.get(
            f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration",
            timeout=5
        )
        if response.status_code == 200:
            print_success("Keycloak is accessible")
            return True
        else:
            print_error(f"Keycloak health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Keycloak health check failed: {e}")
        return False

def test_unauthenticated_endpoints():
    """Test endpoints that don't require authentication"""
    print_info("Testing unauthenticated endpoints...")
    results = []
    
    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL.replace('/api', '')}/health", timeout=5)
        results.append(response.status_code == 200)
    except Exception as e:
        print_error(f"Health endpoint failed: {e}")
        results.append(False)
    
    # Test device status endpoint (public)
    try:
        # This will fail if no devices exist, but should return 404 not 401
        response = requests.get(f"{BASE_URL}/devices/status/test-device-id", timeout=5)
        results.append(response.status_code in [200, 404])  # 404 is OK, 401 means auth required
    except Exception as e:
        print_error(f"Device status endpoint failed: {e}")
        results.append(False)
    
    if all(results):
        print_success("Unauthenticated endpoints working correctly")
        return True
    else:
        print_warning("Some unauthenticated endpoints may have issues")
        return False

def test_authenticated_endpoints(token: str):
    """Test endpoints that require authentication"""
    print_info("Testing authenticated endpoints...")
    headers = {"Authorization": f"Bearer {token}"}
    results = []
    
    # Test users endpoint
    try:
        response = requests.get(f"{BASE_URL}/users", headers=headers, timeout=5)
        results.append(response.status_code == 200)
        if response.status_code == 200:
            print_success("Users endpoint accessible")
        else:
            print_error(f"Users endpoint failed: {response.status_code}")
    except Exception as e:
        print_error(f"Users endpoint failed: {e}")
        results.append(False)
    
    # Test devices endpoint
    try:
        response = requests.get(f"{BASE_URL}/devices", headers=headers, timeout=5)
        results.append(response.status_code == 200)
        if response.status_code == 200:
            print_success("Devices endpoint accessible")
        else:
            print_error(f"Devices endpoint failed: {response.status_code}")
    except Exception as e:
        print_error(f"Devices endpoint failed: {e}")
        results.append(False)
    
    # Test policies endpoint
    try:
        response = requests.get(f"{BASE_URL}/policies", headers=headers, timeout=5)
        results.append(response.status_code == 200)
        if response.status_code == 200:
            print_success("Policies endpoint accessible")
        else:
            print_error(f"Policies endpoint failed: {response.status_code}")
    except Exception as e:
        print_error(f"Policies endpoint failed: {e}")
        results.append(False)
    
    # Test access logs endpoint
    try:
        response = requests.get(f"{BASE_URL}/access/logs", headers=headers, timeout=5)
        results.append(response.status_code == 200)
        if response.status_code == 200:
            print_success("Access logs endpoint accessible")
        else:
            print_error(f"Access logs endpoint failed: {response.status_code}")
    except Exception as e:
        print_error(f"Access logs endpoint failed: {e}")
        results.append(False)
    
    # Test audit logs endpoint
    try:
        response = requests.get(f"{BASE_URL}/audit/logs", headers=headers, timeout=5)
        results.append(response.status_code == 200)
        if response.status_code == 200:
            print_success("Audit logs endpoint accessible")
        else:
            print_error(f"Audit logs endpoint failed: {response.status_code}")
    except Exception as e:
        print_error(f"Audit logs endpoint failed: {e}")
        results.append(False)
    
    if all(results):
        print_success("All authenticated endpoints working correctly")
        return True
    else:
        print_warning("Some authenticated endpoints may have issues")
        return False

def test_policy_evaluation(token: str):
    """Test policy evaluation functionality"""
    print_info("Testing policy evaluation...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # First, create a test policy
    try:
        policy_data = {
            "name": "Test Policy",
            "description": "Test policy for integration testing",
            "policy_type": "access",
            "rules": {
                "conditions": {
                    "device_compliant": True
                },
                "action": "allow"
            },
            "priority": 100,
            "enforce_mode": "enforce"
        }
        response = requests.post(
            f"{BASE_URL}/policies",
            headers=headers,
            json=policy_data,
            timeout=5
        )
        if response.status_code in [200, 201]:
            print_success("Policy creation endpoint working")
            policy_id = response.json().get("id")
            
            # Test policy retrieval
            response = requests.get(
                f"{BASE_URL}/policies/{policy_id}",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                print_success("Policy retrieval working")
                return True
            else:
                print_warning("Policy retrieval failed")
                return False
        else:
            print_warning(f"Policy creation failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Policy evaluation test failed: {e}")
        return False

def test_token_service(token: str):
    """Test token service endpoints"""
    print_info("Testing token service...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test token verify endpoint
    try:
        verify_data = {"token": token}
        response = requests.post(
            f"{BASE_URL}/tokens/verify",
            json=verify_data,
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("valid"):
                print_success("Token verification endpoint working")
                return True
            else:
                print_warning("Token verification returned invalid")
                return False
        else:
            print_warning(f"Token verification failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Token service test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}ZTNA Platform Integration Test Suite{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    results = []
    
    # Test 1: Health checks
    results.append(("Health Check", test_health_check()))
    results.append(("Keycloak Health", test_keycloak_health()))
    
    # Test 2: Unauthenticated endpoints
    results.append(("Unauthenticated Endpoints", test_unauthenticated_endpoints()))
    
    # Test 3: Get authentication token (manual step)
    print_info("\nTo test authenticated endpoints, you need to:")
    print_info("1. Log in via frontend at http://localhost:3000")
    print_info("2. Get the access token from browser DevTools → Application → Local Storage")
    print_info("3. Run this script with: python test_integration_complete.py <token>")
    
    if len(sys.argv) > 1:
        token = sys.argv[1]
        print_info(f"\nUsing provided token (length: {len(token)})")
        
        # Test 4: Authenticated endpoints
        results.append(("Authenticated Endpoints", test_authenticated_endpoints(token)))
        
        # Test 5: Policy evaluation
        results.append(("Policy Evaluation", test_policy_evaluation(token)))
        
        # Test 6: Token service
        results.append(("Token Service", test_token_service(token)))
    else:
        print_warning("\nSkipping authenticated tests (no token provided)")
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Test Summary{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{test_name:.<50} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("All tests passed!")
        return 0
    else:
        print_error(f"{total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

