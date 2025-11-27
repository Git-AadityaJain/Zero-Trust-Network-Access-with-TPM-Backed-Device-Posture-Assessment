# app/schemas/device_state.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DeviceStateResponse(BaseModel):
    """Response for current device state check"""
    has_dpa: bool
    tpm_key_match: bool
    is_compliant: bool
    is_enrolled: bool
    device_id: Optional[int] = None
    device_name: Optional[str] = None
    device_unique_id: Optional[str] = None
    last_posture_time: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    compliance_score: Optional[float] = None
    violations: Optional[List[str]] = None
    posture_data: Optional[dict] = None
    message: str

