"""Force reload of posture_service module"""
import sys
import importlib

# Remove from cache if exists
if 'app.services.posture_service' in sys.modules:
    del sys.modules['app.services.posture_service']
if 'app.services' in sys.modules:
    del sys.modules['app.services']

# Force reload
from app.services.posture_service import PostureService
import importlib
importlib.reload(sys.modules['app.services.posture_service'])

# Test the function
test_data = {
    "antivirus": {"installed": True, "running": True},
    "firewall": {"firewall_enabled": True},
    "disk_encryption": {"encryption_enabled": False},
    "screen_lock": {"screen_lock_enabled": True}
}

result = PostureService.evaluate_compliance(test_data)
print(f"Test result: Compliant={result[0]}, Score={result[1]}%, Violations={result[2]}")

