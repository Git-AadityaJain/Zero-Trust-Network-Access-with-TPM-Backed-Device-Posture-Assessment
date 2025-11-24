"""
CLI for requesting resource access with posture submission

This CLI tool allows DPA to request access to a resource, automatically
submitting fresh posture data with the request.
"""
import sys
import os
import argparse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from dpa.core.access_request import AccessRequestHandler
from dpa.core.enrollment import DeviceEnrollment
from dpa.utils.logger import setup_logger
from dpa.config.settings import config_manager

def main():
    parser = argparse.ArgumentParser(description="DPA Resource Access Request CLI")
    parser.add_argument("--backend-url", type=str, help="Override backend URL")
    parser.add_argument("--device-id", type=int, required=True, help="Device ID (from backend)")
    parser.add_argument("--resource", type=str, required=True, help="Resource identifier")
    parser.add_argument("--access-type", type=str, default="read", choices=["read", "write", "execute"], help="Access type")
    parser.add_argument("--auth-token", type=str, help="JWT authentication token")
    
    args = parser.parse_args()
    
    setup_logger()
    
    # Check if device is enrolled
    enrollment = DeviceEnrollment()
    if not enrollment.is_enrolled():
        print("❌ Device is not enrolled. Please enroll first:")
        print("   python -m dpa.cli.enroll_cli --enrollment-code YOUR_CODE")
        sys.exit(1)
    
    # Create access request handler
    handler = AccessRequestHandler(
        backend_url=args.backend_url or config_manager.get().backend_url
    )
    
    print("=" * 60)
    print("DPA Resource Access Request")
    print("=" * 60)
    print(f"Device ID: {args.device_id}")
    print(f"Resource: {args.resource}")
    print(f"Access Type: {args.access_type}")
    print(f"Backend URL: {handler.backend_url}")
    print("=" * 60)
    print()
    print("Collecting fresh posture data and requesting access...")
    print()
    
    # Request access
    result = handler.request_access(
        device_id=args.device_id,
        resource=args.resource,
        access_type=args.access_type,
        auth_token=args.auth_token
    )
    
    # Display results
    if result.get("allowed"):
        print("✓ Access GRANTED")
        if result.get("token"):
            print(f"\nAccess Token: {result['token']}")
        if result.get("reason"):
            print(f"Reason: {result['reason']}")
    else:
        print("✗ Access DENIED")
        if result.get("reason"):
            print(f"Reason: {result['reason']}")
        if result.get("policy_name"):
            print(f"Policy: {result['policy_name']}")
    
    print()
    return 0 if result.get("allowed") else 1

if __name__ == "__main__":
    sys.exit(main())

