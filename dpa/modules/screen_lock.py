"""
Windows Screen Lock (Screensaver) detection
"""
import subprocess
import logging
import platform

logger = logging.getLogger("dpa.screen_lock")

def check_screen_lock() -> dict:
    """
    Check Windows screen lock/screensaver status
    
    Returns:
        dict: Screen lock status information
    """
    try:
        if platform.system() != "Windows":
            return {
                "screen_lock_enabled": False,
                "method": "Not supported on this OS"
            }
        
        # Check screensaver registry setting
        # HKCU:\Control Panel\Desktop\ScreenSaveActive (1 = enabled, 0 = disabled)
        result = subprocess.run(
            ["powershell", "-Command", "Get-ItemProperty -Path 'HKCU:\\Control Panel\\Desktop' -Name ScreenSaveActive -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ScreenSaveActive"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            try:
                screen_save_active = int(result.stdout.strip())
                screen_lock_enabled = screen_save_active == 1
                
                # Also check screensaver timeout (how long before it activates)
                timeout_result = subprocess.run(
                    ["powershell", "-Command", "Get-ItemProperty -Path 'HKCU:\\Control Panel\\Desktop' -Name ScreenSaveTimeOut -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ScreenSaveTimeOut"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                timeout_seconds = 0
                if timeout_result.returncode == 0 and timeout_result.stdout.strip():
                    try:
                        timeout_seconds = int(timeout_result.stdout.strip())
                    except ValueError:
                        pass
                
                return {
                    "screen_lock_enabled": screen_lock_enabled,
                    "timeout_seconds": timeout_seconds,
                    "method": "Screensaver"
                }
            except ValueError:
                logger.warning(f"Invalid screensaver registry value: {result.stdout.strip()}")
        
        # Fallback: check if screensaver is configured via Group Policy
        gp_result = subprocess.run(
            ["powershell", "-Command", "Get-ItemProperty -Path 'HKLM:\\Software\\Policies\\Microsoft\\Windows\\Control Panel\\Desktop' -Name ScreenSaveActive -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ScreenSaveActive"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if gp_result.returncode == 0 and gp_result.stdout.strip():
            try:
                screen_save_active = int(gp_result.stdout.strip())
                screen_lock_enabled = screen_save_active == 1
                return {
                    "screen_lock_enabled": screen_lock_enabled,
                    "timeout_seconds": 0,
                    "method": "Group Policy"
                }
            except ValueError:
                pass
        
        # Default: assume not enabled if we can't determine
        logger.warning("Could not determine screen lock status")
        return {
            "screen_lock_enabled": False,
            "timeout_seconds": 0,
            "method": "Unknown"
        }
        
    except Exception as e:
        logger.error(f"Error checking screen lock: {e}")
        return {
            "screen_lock_enabled": False,
            "timeout_seconds": 0,
            "method": "Error"
        }

