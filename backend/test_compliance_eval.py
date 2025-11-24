"""Test compliance evaluation with actual data"""
import sys
sys.path.insert(0, '/app')

from app.services.posture_service import PostureService

# Use the actual data structure from the database
test_data = {
    "device_id": "3054898e-8d69-4e80-bebf-4bc6fc7e1b61",
    "timestamp": "2025-11-24T20:09:05.607653Z",
    "os_info": {
        "hostname": "Shubham",
        "system": "Windows",
        "version": "10.0.26100",
        "release": "11",
        "os_type": "Windows",
        "os_version": "11 10.0.26100",
        "device_model": "AMD64",
        "manufacturer": "Unknown"
    },
    "firewall": {
        "firewall_enabled": True,
        "firewall_profile": "Domain"
    },
    "disk_encryption": {
        "encryption_enabled": False,
        "encryption_method": "None"
    },
    "antivirus": {
        "installed": True,
        "running": True,
        "product_name": "Windows Defender"
    },
    "fingerprint": {
        "fingerprint_enabled": True,
        "users_enrolled": 1,
        "fingerprint_hash": "71546855d6279ef70d20909b292c42c2dcb02cd06bde01485da52d13e304ebf4",
        "motherboard_serial": "",
        "bios_serial": "",
        "system_uuid": ""
    }
}

print("=" * 60)
print("Testing Compliance Evaluation")
print("=" * 60)
print()

is_compliant, score, violations = PostureService.evaluate_compliance(test_data)

print(f"Result: {'COMPLIANT' if is_compliant else 'NON-COMPLIANT'}")
print(f"Score: {score}%")
print(f"Violations: {violations}")
print()

# Expected: Should be compliant (antivirus and firewall enabled, only disk encryption missing)
# Score should be: 100 - 25 = 75% (compliant threshold is 70%)
expected_score = 75
expected_violations = ["Disk encryption not enabled"]

print("=" * 60)
print("Expected vs Actual:")
print("=" * 60)
print(f"Expected Score: {expected_score}%")
print(f"Actual Score: {score}%")
print(f"Match: {'✓' if score == expected_score else '✗'}")
print()
print(f"Expected Violations: {expected_violations}")
print(f"Actual Violations: {violations}")
print(f"Match: {'✓' if violations == expected_violations else '✗'}")

