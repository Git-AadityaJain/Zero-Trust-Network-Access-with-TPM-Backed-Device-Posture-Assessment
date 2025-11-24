"""
Posture data collection with device identification
"""
from datetime import datetime, timezone
from typing import Optional


def collect_posture_report() -> dict:
    """
    Collect comprehensive posture information including device ID
    """
    from .os_info import get_os_info
    from .firewall import check_firewall
    from .disk_encryption import check_disk_encryption
    from .antivirus import check_antivirus
    from .screen_lock import check_screen_lock
    from .fingerprint import get_device_fingerprint
    
    # Get device_id from enrollment if available
    device_id = _get_device_id()
    
    report = {
        "device_id": device_id,
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "os_info": get_os_info(),
        "firewall": check_firewall(),
        "disk_encryption": check_disk_encryption(),
        "antivirus": check_antivirus(),
        "screen_lock": check_screen_lock(),
        "fingerprint": get_device_fingerprint()
    }
    
    return report


def _get_device_id() -> str:
    """
    Get device ID from enrollment file
    Returns 'unknown' if not enrolled yet
    """
    try:
        from ..core.enrollment import DeviceEnrollment
        enrollment = DeviceEnrollment()
        device_info = enrollment.get_device_info()
        return device_info.get("device_id") if device_info else "unknown"
    except Exception:
        return "unknown"
