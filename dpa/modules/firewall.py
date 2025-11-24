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
            # Check if any profile shows "state" followed by "on" (more flexible matching)
            # The output format is: "State                                 ON" or "State                                 OFF"
            firewall_enabled = "state" in output and ("on" in output.split("state")[-1][:50])
            
            # Determine profile (check which profile is active)
            profile = "Unknown"
            if "domain profile" in output:
                profile = "Domain"
            elif "private profile" in output:
                profile = "Private"
            elif "public profile" in output:
                profile = "Public"
            
            # More robust check: if we see "state" and "on" anywhere in the output
            if not firewall_enabled:
                # Try alternative: check if all profiles show ON
                lines = result.stdout.split('\n')
                on_count = sum(1 for line in lines if 'state' in line.lower() and 'on' in line.lower())
                firewall_enabled = on_count > 0
            
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
