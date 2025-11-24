# app/schemas/device.py

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class DeviceBase(BaseModel):
    """Base device schema"""
    device_name: str = Field(..., min_length=1, max_length=255)
    os_type: Optional[str] = Field(None, max_length=50)
    os_version: Optional[str] = Field(None, max_length=255)
    device_model: Optional[str] = Field(None, max_length=255)
    manufacturer: Optional[str] = Field(None, max_length=255)


class DeviceEnrollmentRequest(BaseModel):
    """Request payload from DPA agent during enrollment (no auth required)"""
    enrollment_code: str = Field(..., min_length=1)
    device_name: str = Field(..., min_length=1, max_length=255)
    fingerprint_hash: str = Field(..., min_length=64, max_length=64)  # SHA256 hardware fingerprint
    tpm_public_key: str = Field(..., min_length=1)  # PEM-encoded RSA public key
    
    # Device info
    os_type: str = Field(..., max_length=50)
    os_version: Optional[str] = Field(None, max_length=255)
    device_model: Optional[str] = Field(None, max_length=255)
    manufacturer: Optional[str] = Field(None, max_length=255)
    
    # Initial posture data
    initial_posture: Optional[Dict[str, Any]] = None


class DeviceEnrollmentResponse(BaseModel):
    """Response sent to DPA agent after enrollment"""
    device_id: str  # device_unique_id (UUID)
    status: str  # "pending" - awaiting admin approval
    message: str


class DeviceStatusResponse(BaseModel):
    """Response for DPA agent status check"""
    device_id: str
    status: str  # pending/active/rejected/inactive
    is_approved: bool
    message: str


class DeviceUpdate(BaseModel):
    """Admin update schema"""
    device_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    is_compliant: Optional[bool] = None
    posture_data: Optional[Dict[str, Any]] = None
    last_posture_check: Optional[datetime] = None


class DeviceResponse(BaseModel):
    """Full device details (for admin)"""
    id: int
    device_unique_id: str
    device_name: str
    fingerprint_hash: Optional[str]
    status: str
    
    # Device info
    os_type: Optional[str]
    os_version: Optional[str]
    device_model: Optional[str]
    manufacturer: Optional[str]
    
    # User association
    user_id: Optional[int]
    
    # Status flags
    is_enrolled: bool
    is_compliant: bool
    is_active: bool
    
    # Timestamps
    enrolled_at: datetime
    last_seen_at: Optional[datetime]
    last_posture_check: Optional[datetime]
    
    # Posture data
    posture_data: Optional[Dict[str, Any]]
    initial_posture: Optional[Dict[str, Any]]
    
    model_config = ConfigDict(from_attributes=True)


class DeviceApprovalRequest(BaseModel):
    """Request to approve a device and create user"""
    username: str = Field(..., min_length=3, max_length=255)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    temporary_password: str = Field(..., min_length=8)
    assign_roles: Optional[list[str]] = Field(default=["dpa-device"])


class DeviceAssignmentRequest(BaseModel):
    """Request to assign device to existing user"""
    user_id: int = Field(..., gt=0)


class DeviceRejectionRequest(BaseModel):
    """Request to reject device enrollment"""
    rejection_reason: Optional[str] = Field(None, max_length=500)
