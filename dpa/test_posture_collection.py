"""
Test script to see what posture data is being collected
Run this to verify what the DPA detects on your system
"""
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dpa.modules.posture import collect_posture_report
from dpa.utils.logger import setup_logger

def main():
    setup_logger()
    
    print("=" * 60)
    print("DPA Posture Data Collection Test")
    print("=" * 60)
    print()
    
    # Collect posture report
    report = collect_posture_report()
    
    # Pretty print the report
    print("Collected Posture Data:")
    print(json.dumps(report, indent=2))
    print()
    print("=" * 60)
    print("Key Values for Compliance Check:")
    print("=" * 60)
    
    # Extract key values
    antivirus = report.get("antivirus", {})
    firewall = report.get("firewall", {})
    disk_encryption = report.get("disk_encryption", {})
    screen_lock = report.get("screen_lock", {})
    
    print(f"Antivirus:")
    print(f"  - Installed: {antivirus.get('installed', False)}")
    print(f"  - Running: {antivirus.get('running', False)}")
    print(f"  - Product: {antivirus.get('product_name', 'Unknown')}")
    print()
    
    print(f"Firewall:")
    print(f"  - Enabled: {firewall.get('firewall_enabled', False)}")
    print(f"  - Profile: {firewall.get('firewall_profile', 'Unknown')}")
    print()
    
    print(f"Disk Encryption:")
    print(f"  - Enabled: {disk_encryption.get('encryption_enabled', False)}")
    print(f"  - Method: {disk_encryption.get('encryption_method', 'Unknown')}")
    print()
    
    print(f"Screen Lock:")
    print(f"  - Enabled: {screen_lock.get('screen_lock_enabled', False)}")
    print(f"  - Timeout: {screen_lock.get('timeout_seconds', 0)} seconds")
    print(f"  - Method: {screen_lock.get('method', 'Unknown')}")
    print()
    
    print("=" * 60)
    print("Manual Verification Commands:")
    print("=" * 60)
    print()
    print("1. Check Antivirus:")
    print("   PowerShell: Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | Select-Object displayName, productState")
    print()
    print("2. Check Firewall:")
    print("   Command: netsh advfirewall show allprofiles state")
    print()
    print("3. Check BitLocker:")
    print("   PowerShell: Get-BitLockerVolume | Select-Object MountPoint, ProtectionStatus")
    print()
    print("4. Check Screen Lock (Group Policy):")
    print("   PowerShell: Get-ItemProperty -Path 'HKLM:\\Software\\Policies\\Microsoft\\Windows\\Control Panel\\Desktop' -Name ScreenSaveActive")
    print()

if __name__ == "__main__":
    main()

