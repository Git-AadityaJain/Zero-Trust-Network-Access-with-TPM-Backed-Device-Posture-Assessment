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
        # Try to get BitLocker volume info with both MountPoint and ProtectionStatus
        result = subprocess.run(
            ["powershell", "-Command", "Get-BitLockerVolume | Where-Object { $_.MountPoint -eq 'C:' } | Select-Object MountPoint, ProtectionStatus, VolumeStatus | ConvertTo-Json -Depth 2"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            import json
            try:
                volume_data = json.loads(result.stdout)
                
                if not isinstance(volume_data, list):
                    volume_data = [volume_data] if volume_data else []
                
                # Check if C: drive data exists
                c_drive = next((v for v in volume_data if v.get("MountPoint") == "C:"), None)
                
                if c_drive:
                    protection_status = c_drive.get("ProtectionStatus")
                    volume_status = c_drive.get("VolumeStatus", "")
                    
                    # Handle both numeric (1/0) and string ("On"/"Off") formats
                    if isinstance(protection_status, str):
                        encryption_enabled = protection_status.lower() in ["on", "1", "true"]
                    elif isinstance(protection_status, int):
                        encryption_enabled = protection_status == 1  # 1 = On, 0 = Off
                    else:
                        # Fallback: check VolumeStatus
                        encryption_enabled = "encrypted" in str(volume_status).lower() if volume_status else False
                    
                    return {
                        "encryption_enabled": encryption_enabled,
                        "encryption_method": "BitLocker" if encryption_enabled else "None"
                    }
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse BitLocker JSON: {e}, output: {result.stdout[:100]}")
        
        # Fallback: try simpler command
        result2 = subprocess.run(
            ["powershell", "-Command", "(Get-BitLockerVolume -MountPoint 'C:' -ErrorAction SilentlyContinue).ProtectionStatus"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result2.returncode == 0 and result2.stdout.strip():
            protection_status = result2.stdout.strip()
            if isinstance(protection_status, str):
                encryption_enabled = protection_status.lower() in ["on", "1", "true"]
            else:
                encryption_enabled = str(protection_status) == "1"
            
            return {
                "encryption_enabled": encryption_enabled,
                "encryption_method": "BitLocker" if encryption_enabled else "None"
            }
        
        # If we get here, BitLocker check failed (likely permission issue)
        # Default to False (not encrypted) since we can't verify
        logger.warning("Failed to check BitLocker status via PowerShell (may require admin privileges)")
        return {
            "encryption_enabled": False,
            "encryption_method": "None"
        }
        
    except subprocess.TimeoutExpired:
        logger.warning("BitLocker check timed out")
        return {
            "encryption_enabled": False,
            "encryption_method": "None"
        }
    except Exception as e:
        logger.error(f"Error checking disk encryption: {e}")
        # Default to not encrypted if we can't determine
        return {
            "encryption_enabled": False,
            "encryption_method": "None"
        }
