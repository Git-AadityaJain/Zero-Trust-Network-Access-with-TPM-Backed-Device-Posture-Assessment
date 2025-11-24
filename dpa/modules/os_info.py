import platform
import socket

def get_os_info():
    """Get OS information including hostname"""
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "unknown"
    
    system = platform.system()
    version = platform.version()
    release = platform.release()
    
    # Determine OS type
    if system == "Windows":
        os_type = "Windows"
        os_version = f"{release} {version}"
    elif system == "Linux":
        os_type = "Linux"
        os_version = f"{release} {version}"
    elif system == "Darwin":
        os_type = "macOS"
        os_version = f"{release} {version}"
    else:
        os_type = system
        os_version = version
    
    return {
        "hostname": hostname,
        "system": system,
        "version": version,
        "release": release,
        "os_type": os_type,
        "os_version": os_version,
        "device_model": platform.machine(),
        "manufacturer": "Unknown"  # Would need additional detection for manufacturer
    }
