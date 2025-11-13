# routers/device.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.device import (
    DeviceResponse,
    DeviceUpdate,
    DeviceEnrollmentRequest
)
from app.services.device_service import DeviceService
from app.services.enrollment_service import EnrollmentService
from app.services.audit_service import AuditService
from app.dependencies.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/devices", tags=["devices"])

@router.post("/enroll", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def enroll_device(
    enrollment_data: DeviceEnrollmentRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Enroll a new device with enrollment code"""
    
    # Validate enrollment code
    is_valid, error_message = await EnrollmentService.validate_code(
        db, enrollment_data.enrollment_code
    )
    
    if not is_valid:
        await AuditService.log_event(
            db=db,
            user_id=current_user.id,
            event_type="device_enrollment",
            action="enroll",
            status="failure",
            description=f"Failed enrollment: {error_message}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Check if device already exists
    existing_device = await DeviceService.get_device_by_unique_id(
        db, enrollment_data.device_unique_id
    )
    
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device already enrolled"
        )
    
    # Create device
    from app.schemas.device import DeviceCreate
    device_create = DeviceCreate(
        user_id=current_user.id,
        device_name=enrollment_data.device_name,
        device_unique_id=enrollment_data.device_unique_id,
        tpm_public_key=enrollment_data.tpm_public_key,
        os_type=enrollment_data.os_type,
        os_version=enrollment_data.os_version,
        device_model=enrollment_data.device_model,
        manufacturer=enrollment_data.manufacturer
    )
    
    device = await DeviceService.create_device(db, device_create)
    
    # Mark enrollment code as used
    await EnrollmentService.use_code(db, enrollment_data.enrollment_code)
    
    # Log successful enrollment
    await AuditService.log_event(
        db=db,
        user_id=current_user.id,
        event_type="device_enrollment",
        action="enroll",
        resource_type="device",
        resource_id=str(device.id),
        status="success",
        description=f"Device {device.device_name} enrolled successfully"
    )
    
    return device

@router.get("", response_model=List[DeviceResponse])  # Changed from "/" to ""
async def list_user_devices(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    active_only: bool = False
):
    """List all devices for current user"""
    devices = await DeviceService.get_devices_by_user(db, current_user.id, active_only)
    return devices

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get device by ID"""
    device = await DeviceService.get_device_by_id(db, device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Ensure user owns the device
    if device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return device

@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update device information"""
    device = await DeviceService.get_device_by_id(db, device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Ensure user owns the device
    if device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    updated_device = await DeviceService.update_device(db, device_id, device_update)
    return updated_device

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a device"""
    device = await DeviceService.get_device_by_id(db, device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Ensure user owns the device
    if device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await DeviceService.delete_device(db, device_id)
    
    # Log deletion
    await AuditService.log_event(
        db=db,
        user_id=current_user.id,
        event_type="device_management",
        action="delete",
        resource_type="device",
        resource_id=str(device_id),
        status="success"
    )
