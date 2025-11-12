"""
Device fingerprinting for unique identification
"""
import platform
import subprocess
import hashlib
import logging

logger = logging.getLogger("dpa.fingerprint")

def get_device_fingerprint() -> dict:
    """
    Generate device fingerprint based on hardware identifiers
    
    Returns:
        dict: Device fingerprint information
    """
    try:
        # Get motherboard serial
        mb_serial = _get_motherboard_serial()
        
        # Get BIOS serial
        bios_serial = _get_bios_serial()
        
        # Get system UUID
        system_uuid = _get_system_uuid()
        
        # Create composite fingerprint hash
        fingerprint_data = f"{mb_serial}:{bios_serial}:{system_uuid}"
        fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        
        return {
            "fingerprint_enabled": True,
            "users_enrolled": 1,  # Placeholder
            "fingerprint_hash": fingerprint_hash[:16]  # Truncated for display
        }
    except Exception as e:
        logger.error(f"Error generating device fingerprint: {e}")
        return {
            "fingerprint_enabled": False,
            "users_enrolled": 0,
            "fingerprint_hash": "unknown"
        }

def _get_motherboard_serial() -> str:
    """Get motherboard serial number"""
    try:
        result = subprocess.run(
            ["wmic", "baseboard", "get", "serialnumber"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                return lines[1].strip()
    except Exception:
        pass
    return "unknown_mb"

def _get_bios_serial() -> str:
    """Get BIOS serial number"""
    try:
        result = subprocess.run(
            ["wmic", "bios", "get", "serialnumber"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                return lines[1].strip()
    except Exception:
        pass
    return "unknown_bios"

def _get_system_uuid() -> str:
    """Get system UUID"""
    try:
        result = subprocess.run(
            ["wmic", "csproduct", "get", "uuid"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                return lines[1].strip()
    except Exception:
        pass
    return "unknown_uuid"
