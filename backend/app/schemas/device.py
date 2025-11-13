# schemas/device.py

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class DeviceBase(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=255)
    os_type: Optional[str] = Field(None, max_length=50)
    os_version: Optional[str] = Field(None, max_length=255)
    device_model: Optional[str] = Field(None, max_length=255)
    manufacturer: Optional[str] = Field(None, max_length=255)

class DeviceCreate(DeviceBase):
    device_unique_id: str = Field(..., max_length=512)
    user_id: int
    tpm_public_key: Optional[str] = None
    attestation_data: Optional[Dict[str, Any]] = None

class DeviceUpdate(BaseModel):
    device_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    is_compliant: Optional[bool] = None
    posture_data: Optional[Dict[str, Any]] = None
    last_posture_check: Optional[datetime] = None

class DeviceResponse(DeviceBase):
    id: int
    device_unique_id: str
    user_id: int
    is_enrolled: bool
    is_compliant: bool
    is_active: bool
    enrolled_at: datetime
    last_seen_at: datetime
    last_posture_check: Optional[datetime]
    posture_data: Optional[Dict[str, Any]]
    
    model_config = ConfigDict(from_attributes=True)

class DeviceEnrollmentRequest(BaseModel):
    enrollment_code: str = Field(..., min_length=1)
    device_name: str = Field(..., min_length=1, max_length=255)
    device_unique_id: str = Field(..., max_length=512)
    tpm_public_key: str
    os_type: str = Field(..., max_length=50)
    os_version: Optional[str] = Field(None, max_length=255)
    device_model: Optional[str] = Field(None, max_length=255)
    manufacturer: Optional[str] = Field(None, max_length=255)
