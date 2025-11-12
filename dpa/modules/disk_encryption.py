"""
Windows Disk Encryption (BitLocker) detection
"""
import subprocess
import logging

logger = logging.getLogger("dpa.disk_encryption")

def check_disk_encryption() -> dict:
    """
    Check BitLocker disk encryption status
    
    Returns:
        dict: Disk encryption status information
    """
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-BitLockerVolume | Select-Object MountPoint, ProtectionStatus | ConvertTo-Json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            import json
            volumes = json.loads(result.stdout)
            
            if not isinstance(volumes, list):
                volumes = [volumes]
            
            # Check if C: drive is encrypted
            c_drive = next((v for v in volumes if v.get("MountPoint") == "C:"), None)
            
            if c_drive:
                protection_status = c_drive.get("ProtectionStatus", 0)
                encryption_enabled = protection_status == 1  # 1 = On, 0 = Off
                
                return {
                    "encryption_enabled": encryption_enabled,
                    "encryption_method": "BitLocker" if encryption_enabled else "None"
                }
        
        logger.warning("Failed to check BitLocker status via PowerShell")
        return {
            "encryption_enabled": False,
            "encryption_method": "Unknown"
        }
        
    except Exception as e:
        logger.error(f"Error checking disk encryption: {e}")
        return {
            "encryption_enabled": False,
            "encryption_method": "Unknown"
        }
