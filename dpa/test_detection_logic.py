"""
Test the actual detection logic used by DPA modules
This will show exactly what each module detects and why
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dpa.modules.antivirus import check_antivirus
from dpa.modules.firewall import check_firewall
from dpa.modules.disk_encryption import check_disk_encryption
from dpa.modules.screen_lock import check_screen_lock
from dpa.utils.logger import setup_logger

def main():
    setup_logger()
    
    print("=" * 70)
    print("DPA Detection Logic Test")
    print("=" * 70)
    print()
    
    # Test Antivirus
    print("1. ANTIVIRUS DETECTION:")
    print("-" * 70)
    print("Logic: Get-CimInstance from SecurityCenter2")
    print("Checks: productState bit 12-15 (0x1000 = running)")
    print()
    av_result = check_antivirus()
    print(f"Result: {av_result}")
    print(f"  - Installed: {av_result.get('installed')}")
    print(f"  - Running: {av_result.get('running')}")
    print(f"  - Product: {av_result.get('product_name')}")
    print(f"  - Backend will check: installed=True AND running=True")
    print(f"  - Status: {'ENABLED' if av_result.get('installed') and av_result.get('running') else 'DISABLED'}")
    print()
    
    # Test Firewall
    print("2. FIREWALL DETECTION:")
    print("-" * 70)
    print("Logic: netsh advfirewall show allprofiles state")
    print("Checks: Looks for 'state' and 'on' in output")
    print()
    fw_result = check_firewall()
    print(f"Result: {fw_result}")
    print(f"  - Enabled: {fw_result.get('firewall_enabled')}")
    print(f"  - Profile: {fw_result.get('firewall_profile')}")
    print(f"  - Backend will check: firewall_enabled=True")
    print(f"  - Status: {'ENABLED' if fw_result.get('firewall_enabled') else 'DISABLED'}")
    print()
    
    # Test Disk Encryption
    print("3. DISK ENCRYPTION (BitLocker) DETECTION:")
    print("-" * 70)
    print("Logic: Get-BitLockerVolume for C: drive")
    print("Checks: ProtectionStatus == 'On' or 1")
    print("Note: Requires admin privileges, defaults to False if fails")
    print()
    de_result = check_disk_encryption()
    print(f"Result: {de_result}")
    print(f"  - Enabled: {de_result.get('encryption_enabled')}")
    print(f"  - Method: {de_result.get('encryption_method')}")
    print(f"  - Backend will check: encryption_enabled=True")
    print(f"  - Status: {'ENABLED' if de_result.get('encryption_enabled') else 'DISABLED'}")
    print()
    
    # Test Screen Lock
    print("4. SCREEN LOCK DETECTION:")
    print("-" * 70)
    print("Logic: Get-ItemProperty from HKCU registry")
    print("Checks: ScreenSaveActive == 1")
    print()
    sl_result = check_screen_lock()
    print(f"Result: {sl_result}")
    print(f"  - Enabled: {sl_result.get('screen_lock_enabled')}")
    print(f"  - Timeout: {sl_result.get('timeout_seconds')} seconds")
    print(f"  - Method: {sl_result.get('method')}")
    print(f"  - Backend will check: screen_lock_enabled=True")
    print(f"  - Status: {'ENABLED' if sl_result.get('screen_lock_enabled') else 'DISABLED'}")
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY - What Backend Will Evaluate:")
    print("=" * 70)
    av_enabled = av_result.get('installed') and av_result.get('running')
    fw_enabled = fw_result.get('firewall_enabled')
    de_enabled = de_result.get('encryption_enabled')
    sl_enabled = sl_result.get('screen_lock_enabled')
    
    print(f"Antivirus:     {'ENABLED' if av_enabled else 'DISABLED'}")
    print(f"Firewall:      {'ENABLED' if fw_enabled else 'DISABLED'}")
    print(f"Disk Encrypt:  {'ENABLED' if de_enabled else 'DISABLED'}")
    print(f"Screen Lock:   {'ENABLED' if sl_enabled else 'DISABLED'}")
    print()
    
    # Calculate expected score
    score = 100
    violations = []
    if not av_enabled:
        score -= 30
        violations.append("Antivirus not enabled")
    if not fw_enabled:
        score -= 25
        violations.append("Firewall not enabled")
    if not de_enabled:
        score -= 25
        violations.append("Disk encryption not enabled")
    if not sl_enabled:
        score -= 10
        violations.append("Screen lock not enabled")
    
    is_compliant = score >= 70
    print(f"Expected Compliance Score: {score}%")
    print(f"Expected Status: {'COMPLIANT' if is_compliant else 'NON-COMPLIANT'}")
    print(f"Expected Violations: {violations}")
    print()

if __name__ == "__main__":
    main()

