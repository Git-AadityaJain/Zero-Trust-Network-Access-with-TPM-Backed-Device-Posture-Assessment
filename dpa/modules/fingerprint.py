"""
Device fingerprinting for unique identification
"""
import platform
import subprocess
import hashlib
import logging
import socket
import uuid as py_uuid

logger = logging.getLogger("dpa.fingerprint")

def get_device_fingerprint() -> dict:
    """
    Generate device fingerprint based on hardware identifiers
    Uses fallback identifiers when primary hardware IDs are unavailable
    
    Returns:
        dict: Device fingerprint information
    """
    try:
        # Get primary hardware identifiers
        mb_serial = _get_motherboard_serial()
        bios_serial = _get_bios_serial()
        system_uuid = _get_system_uuid()
        
        # Get fallback identifiers (used when primary IDs are unavailable)
        computer_name = _get_computer_name()
        mac_address = _get_mac_address()
        machine_guid = _get_machine_guid()
        
        # Check if primary identifiers are all unavailable
        primary_available = (
            mb_serial and mb_serial not in ("unknown_mb", "") and
            bios_serial and bios_serial not in ("unknown_bios", "") and
            system_uuid and system_uuid not in ("unknown_uuid", "")
        )
        
        if primary_available:
            # Use primary hardware identifiers
            fingerprint_data = f"{mb_serial}:{bios_serial}:{system_uuid}"
        else:
            # Use fallback identifiers when primary ones are unavailable
            # Combine computer name, MAC address, and machine GUID for uniqueness
            logger.warning("Primary hardware identifiers unavailable, using fallback identifiers")
            fingerprint_data = f"{computer_name}:{mac_address}:{machine_guid}:{mb_serial}:{bios_serial}:{system_uuid}"
        
        fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        
        return {
            "fingerprint_enabled": True,
            "users_enrolled": 1,  # Placeholder
            "fingerprint_hash": fingerprint_hash,  # Full 64-char SHA256 hash
            "motherboard_serial": mb_serial,
            "bios_serial": bios_serial,
            "system_uuid": system_uuid,
            "computer_name": computer_name,
            "mac_address": mac_address,
            "machine_guid": machine_guid,
            "using_fallback": not primary_available
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
            lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            # Skip header line, get first data line
            for line in lines[1:]:
                serial = line.strip()
                # Check if serial is valid (not empty or placeholder)
                if serial and serial.lower() not in ("", "serialnumber", "to be filled by o.e.m.", "default string", "serial number"):
                    return serial
    except Exception as e:
        logger.debug(f"Error getting motherboard serial: {e}")
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
            lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            # Skip header line, get first data line
            for line in lines[1:]:
                serial = line.strip()
                # Check if serial is valid (not empty or placeholder)
                if serial and serial.lower() not in ("", "serialnumber", "to be filled by o.e.m.", "default string", "serial number"):
                    return serial
    except Exception as e:
        logger.debug(f"Error getting BIOS serial: {e}")
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
            lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            # Skip header line, get first data line
            for line in lines[1:]:
                uuid_value = line.strip()
                # Check if UUID is valid (not empty or placeholder)
                if uuid_value and uuid_value.lower() not in ("", "uuid", "to be filled by o.e.m.", "default string"):
                    return uuid_value
    except Exception as e:
        logger.debug(f"Error getting system UUID: {e}")
    return "unknown_uuid"

def _get_computer_name() -> str:
    """Get computer name / hostname"""
    try:
        return socket.gethostname()
    except Exception:
        return "unknown_host"

def _get_mac_address() -> str:
    """Get MAC address of primary network interface"""
    try:
        # Get MAC address using Python's uuid module
        node = py_uuid.getnode()
        # Check if it's a valid MAC (not random/virtual)
        if node and (node >> 40) & 0xff != 0:  # First byte should not be 0
            mac = ':'.join(['{:02x}'.format((node >> elements) & 0xff) 
                           for elements in range(0, 2*6, 2)][::-1])
            if mac and mac != "00:00:00:00:00:00":
                return mac
    except Exception:
        pass
    
    # Fallback: try wmic to get first physical adapter MAC
    try:
        result = subprocess.run(
            ["wmic", "path", "win32_networkadapter", "where", "PhysicalAdapter=true", "get", "MACAddress"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.strip().split('\n') 
                    if line.strip() and line.strip().upper() != "MACADDRESS"]
            for line in lines:
                if line and line != "00:00:00:00:00:00":
                    # Normalize format (wmic may return with or without colons)
                    mac = line.replace("-", ":").replace(" ", "")
                    if len(mac) == 12:  # Valid MAC without separators
                        mac = ':'.join([mac[i:i+2] for i in range(0, 12, 2)])
                    if mac and mac != "00:00:00:00:00:00":
                        return mac
    except Exception:
        pass
    
    return "unknown_mac"

def _get_machine_guid() -> str:
    """Get Windows Machine GUID from registry"""
    try:
        result = subprocess.run(
            ["reg", "query", "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography", "/v", "MachineGuid"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Parse registry output: "    MachineGuid    REG_SZ    {guid}"
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if "MachineGuid" in line and "REG_SZ" in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith("{") and part.endswith("}"):
                            return part.strip("{}")
    except Exception:
        pass
    
    return "unknown_guid"
