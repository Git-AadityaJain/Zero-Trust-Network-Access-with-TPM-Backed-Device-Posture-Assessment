"""
Windows Firewall status detection
"""
import subprocess
import logging

logger = logging.getLogger("dpa.firewall")

def check_firewall() -> dict:
    """
    Check Windows Firewall status
    
    Returns:
        dict: Firewall status information
    """
    try:
        result = subprocess.run(
            ["netsh", "advfirewall", "show", "allprofiles", "state"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            output = result.stdout.lower()
            firewall_enabled = "state                                 on" in output
            
            # Determine profile
            profile = "Unknown"
            if "domain profile" in output:
                profile = "Domain"
            elif "private profile" in output:
                profile = "Private"
            elif "public profile" in output:
                profile = "Public"
            
            return {
                "firewall_enabled": firewall_enabled,
                "firewall_profile": profile
            }
        else:
            logger.warning("Failed to check firewall status via netsh")
            return {
                "firewall_enabled": False,
                "firewall_profile": "Unknown"
            }
    except Exception as e:
        logger.error(f"Error checking firewall: {e}")
        return {
            "firewall_enabled": False,
            "firewall_profile": "Unknown"
        }
