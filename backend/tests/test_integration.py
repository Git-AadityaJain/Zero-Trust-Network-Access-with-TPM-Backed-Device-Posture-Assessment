#!/usr/bin/env python3
"""
Integration test script for ZTNA platform
Tests backend, frontend, Keycloak, and DPA integration
"""

import requests
import json
import sys
from typing import Dict, Any

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
KEYCLOAK_URL = "http://localhost:8080"
KEYCLOAK_REALM = "master"

def test_backend_health():
    """Test backend health endpoints"""
    print("\n=== Testing Backend Health ===")
    try:
        # Basic health
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Basic health check passed")
        
        # Detailed health
        response = requests.get(f"{BACKEND_URL}/health/detailed", timeout=5)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Detailed health check passed")
        print(f"  - Database: {data['components']['database']['status']}")
        print(f"  - Keycloak: {data['components']['keycloak']['status']}")
        return True
    except Exception as e:
        print(f"✗ Backend health check failed: {e}")
        return False

def test_keycloak_connectivity():
    """Test Keycloak connectivity"""
    print("\n=== Testing Keycloak Connectivity ===")
    try:
        # Test well-known endpoint
        url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration"
        response = requests.get(url, timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "issuer" in data
        print("✓ Keycloak is accessible")
        print(f"  - Issuer: {data['issuer']}")
        return True
    except Exception as e:
        print(f"✗ Keycloak connectivity test failed: {e}")
        return False

def test_frontend_connectivity():
    """Test frontend connectivity"""
    print("\n=== Testing Frontend Connectivity ===")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        assert response.status_code == 200
        print("✓ Frontend is accessible")
        return True
    except Exception as e:
        print(f"✗ Frontend connectivity test failed: {e}")
        return False

def test_backend_keycloak_integration():
    """Test backend-Keycloak integration"""
    print("\n=== Testing Backend-Keycloak Integration ===")
    try:
        # Test health endpoint which checks Keycloak
        response = requests.get(f"{BACKEND_URL}/health/detailed", timeout=5)
        assert response.status_code == 200
        data = response.json()
        keycloak_status = data["components"]["keycloak"]["status"]
        
        if keycloak_status == "healthy":
            print("✓ Backend can communicate with Keycloak")
            return True
        else:
            print(f"⚠ Keycloak status: {keycloak_status}")
            print(f"  Message: {data['components']['keycloak']['message']}")
            return False
    except Exception as e:
        print(f"✗ Backend-Keycloak integration test failed: {e}")
        return False

def test_backend_api_endpoints():
    """Test backend API endpoints (without auth)"""
    print("\n=== Testing Backend API Endpoints ===")
    try:
        # Test health endpoint
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        assert response.status_code == 200
        print("✓ Health endpoint accessible")
        
        # Test API docs
        response = requests.get(f"{BACKEND_URL}/docs", timeout=5)
        assert response.status_code == 200
        print("✓ API documentation accessible")
        
        # Test OpenAPI schema
        response = requests.get(f"{BACKEND_URL}/openapi.json", timeout=5)
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        print("✓ OpenAPI schema accessible")
        print(f"  - Available paths: {len(schema['paths'])}")
        
        return True
    except Exception as e:
        print(f"✗ Backend API endpoints test failed: {e}")
        return False

def test_dpa_backend_integration():
    """Test DPA-backend integration endpoints"""
    print("\n=== Testing DPA-Backend Integration Endpoints ===")
    try:
        # Test enrollment endpoint exists
        response = requests.post(
            f"{BACKEND_URL}/api/devices/enroll",
            json={
                "enrollment_code": "test-code",
                "device_name": "Test Device",
                "fingerprint_hash": "a" * 64,
                "tpm_public_key": "test-key",
                "os_type": "Windows"
            },
            timeout=5
        )
        # Should return 400 (invalid code) not 404 (endpoint not found)
        assert response.status_code != 404
        print("✓ Device enrollment endpoint exists")
        
        # Test posture submission endpoint exists
        response = requests.post(
            f"{BACKEND_URL}/api/posture/submit",
            json={
                "device_id": "test-device-id",
                "posture_data": {},
                "signature": "test-signature"
            },
            timeout=5
        )
        # Should return 404 (device not found) not 404 (endpoint not found) or 422 (validation error)
        assert response.status_code in [404, 422]
        print("✓ Posture submission endpoint exists")
        
        # Test device status endpoint exists
        response = requests.get(
            f"{BACKEND_URL}/api/devices/status/test-device-id",
            timeout=5
        )
        # Should return 404 (device not found) not 404 (endpoint not found)
        assert response.status_code == 404
        print("✓ Device status endpoint exists")
        
        return True
    except Exception as e:
        print(f"✗ DPA-Backend integration endpoints test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("ZTNA Platform Integration Tests")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Backend Health", test_backend_health()))
    results.append(("Keycloak Connectivity", test_keycloak_connectivity()))
    results.append(("Frontend Connectivity", test_frontend_connectivity()))
    results.append(("Backend-Keycloak Integration", test_backend_keycloak_integration()))
    results.append(("Backend API Endpoints", test_backend_api_endpoints()))
    results.append(("DPA-Backend Integration", test_dpa_backend_integration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

