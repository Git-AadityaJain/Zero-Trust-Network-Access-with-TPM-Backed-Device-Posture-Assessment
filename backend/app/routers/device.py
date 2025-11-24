# app/routers/device.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.device import (
    DeviceEnrollmentRequest,
    DeviceEnrollmentResponse,
    DeviceStatusResponse,
    DeviceResponse,
    DeviceUpdate,
    DeviceApprovalRequest,
    DeviceAssignmentRequest,
    DeviceRejectionRequest
)
from app.schemas.user import UserCreate
from app.services.device_service import DeviceService
from app.services.enrollment_service import EnrollmentService
from app.services.user_service import UserService
from app.services.audit_service import AuditService
from app.services.keycloak_service import keycloak_service, KeycloakError
from app.dependencies.auth import get_current_active_user
from app.dependencies.rbac import require_role
from app.models.user import User
from app.config import settings

import logging
import secrets
import string

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/devices", tags=["devices"])


# ==================== PUBLIC ENDPOINTS (No Auth Required) ====================

@router.post("/enroll", response_model=DeviceEnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_device(
    enrollment_data: DeviceEnrollmentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    **PUBLIC ENDPOINT**
    Enroll a new device using an enrollment code (called by DPA agent)
    No authentication required - validates enrollment code instead
    """
    # Validate enrollment code
    is_valid, error_message = await EnrollmentService.validate_code(
        db, enrollment_data.enrollment_code
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message or "Invalid enrollment code"
        )
    
    # Get enrollment code
    enrollment_code = await EnrollmentService.get_code_by_value(
        db, enrollment_data.enrollment_code
    )
    
    # Check if device with same fingerprint already exists
    existing_device = await DeviceService.get_device_by_fingerprint(
        db, enrollment_data.fingerprint_hash
    )
    
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device with this hardware fingerprint already enrolled"
        )
    
    # Enroll device with pending status
    device = await DeviceService.enroll_device(
        db=db,
        enrollment_data=enrollment_data,
        enrollment_code_id=enrollment_code.id
    )
    
    # Mark enrollment code as used
    await EnrollmentService.use_code(db, enrollment_code.code)
    
    logger.info(f"Device enrolled with pending status: {device.device_unique_id}")
    
    return DeviceEnrollmentResponse(
        device_id=device.device_unique_id,
        status="pending",
        message="Device enrolled successfully. Awaiting admin approval."
    )


@router.get("/status/{device_id}", response_model=DeviceStatusResponse)
async def check_device_status(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    **PUBLIC ENDPOINT**
    Check device enrollment status (called by DPA agent)
    Returns approval status without requiring authentication
    """
    device = await DeviceService.get_device_by_unique_id(db, device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    is_approved = device.status == "active" and device.is_enrolled
    
    status_messages = {
        "pending": "Device enrollment pending admin approval",
        "active": "Device is approved and active",
        "rejected": "Device enrollment was rejected",
        "inactive": "Device is inactive"
    }
    
    return DeviceStatusResponse(
        device_id=device.device_unique_id,
        status=device.status,
        is_approved=is_approved,
        message=status_messages.get(device.status, "Unknown status")
    )


@router.delete("/unenroll/{device_unique_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unenroll_device_public(
    device_unique_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    **PUBLIC ENDPOINT**
    Unenroll device by device_unique_id (called by DPA agent)
    Allows device to remove itself from backend without authentication
    Only works if device is in pending or rejected status (not active)
    """
    device = await DeviceService.get_device_by_unique_id(db, device_unique_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Only allow unenrollment if device is pending or rejected
    # Active devices should be deleted by admin to prevent accidental removal
    if device.status == "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot unenroll active device. Please contact administrator to delete device."
        )
    
    # Delete device
    await DeviceService.delete_device(db, device)
    
    logger.info(f"Device {device_unique_id} unenrolled (self-service)")
    return None


# ==================== ADMIN ENDPOINTS (Authenticated) ====================

@router.get("/pending", response_model=List[DeviceResponse])
async def get_pending_devices(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all devices awaiting approval (admin only)
    """
    devices = await DeviceService.get_pending_devices(db)
    return [DeviceResponse.model_validate(device) for device in devices]


@router.get("", response_model=List[DeviceResponse])
async def get_all_devices(
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, active, rejected, inactive"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all devices with optional filtering
    """
    devices = await DeviceService.get_all_devices(
        db=db,
        limit=limit,
        offset=offset,
        status_filter=status_filter
    )
    return [DeviceResponse.model_validate(device) for device in devices]


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get device details by ID
    """
    device = await DeviceService.get_device_by_id(db, device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return DeviceResponse.model_validate(device)


@router.patch("/{device_id}/approve", response_model=DeviceResponse)
async def approve_device(
    device_id: int,
    approval_data: DeviceApprovalRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve device enrollment and create Keycloak user (admin only)
    
    Workflow:
    1. Validate device exists and is pending
    2. Create user in Keycloak
    3. Assign roles to user in Keycloak
    4. Create user in local database
    5. Link device to user
    6. Update device status to active
    """
    # Get device
    device = await DeviceService.get_device_by_id(db, device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if device.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device is not in pending status (current: {device.status})"
        )
    
    try:
        # Step 1: Create user in Keycloak
        logger.info(f"Creating Keycloak user for approved device {device_id}")
        
        keycloak_user_id = await keycloak_service.create_user(
            username=approval_data.username,
            email=approval_data.email,
            first_name=approval_data.first_name,
            last_name=approval_data.last_name,
            enabled=True,
            email_verified=False,
            temporary_password=approval_data.temporary_password,
            attributes={"device_id": [str(device.id)]}
        )
        
        # Step 2: Assign roles in Keycloak
        if approval_data.assign_roles:
            await keycloak_service.assign_realm_roles_to_user(
                user_id=keycloak_user_id,
                role_names=approval_data.assign_roles
            )
        
        # Step 3: Create user in local database
        user = await UserService.create_user(
            db=db,
            user_data=UserCreate(
                keycloak_id=keycloak_user_id,
                username=approval_data.username,
                email=approval_data.email,
                first_name=approval_data.first_name,
                last_name=approval_data.last_name,
                is_active=True,
                email_verified=False
            )
        )
        
        # Step 4: Approve device and link to user
        device = await DeviceService.approve_device(db, device, user.id)
        
        # Step 5: Audit log
        await AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action="device_approved",
            resource_type="device",
            resource_id=device.id,
            details={
                "device_id": device.device_unique_id,
                "approved_by": current_user.username,
                "keycloak_user_id": keycloak_user_id,
                "username": approval_data.username
            }
        )
        
        logger.info(f"Device {device_id} approved and user {user.id} created")
        return DeviceResponse.model_validate(device)
        
    except KeycloakError as e:
        logger.error(f"Keycloak error during device approval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user in Keycloak: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error approving device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve device"
        )


@router.patch("/{device_id}/reject", response_model=DeviceResponse)
async def reject_device(
    device_id: int,
    rejection_data: DeviceRejectionRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Reject device enrollment (admin only)
    """
    device = await DeviceService.get_device_by_id(db, device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if device.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device is not in pending status (current: {device.status})"
        )
    
    # Reject device
    device = await DeviceService.reject_device(
        db, device, rejection_data.rejection_reason
    )
    
    # Audit log
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        action="device_rejected",
        resource_type="device",
        resource_id=device.id,
        details={
            "device_id": device.device_unique_id,
            "rejected_by": current_user.username,
            "reason": rejection_data.rejection_reason
        }
    )
    
    logger.info(f"Device {device_id} rejected by admin {current_user.username}")
    return DeviceResponse.model_validate(device)


@router.patch("/{device_id}/assign", response_model=DeviceResponse)
async def assign_device_to_user(
    device_id: int,
    assignment_data: DeviceAssignmentRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Assign device to an existing user (admin only)
    Use this when device should be linked to an already existing user account
    """
    device = await DeviceService.get_device_by_id(db, device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if device.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device is not in pending status (current: {device.status})"
        )
    
    # Verify user exists
    user = await UserService.get_user_by_id(db, assignment_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Assign device to user
    device = await DeviceService.assign_device_to_user(db, device, user.id)
    
    # Update device_id attribute in Keycloak
    try:
        await keycloak_service.set_user_attribute(
            user_id=user.keycloak_id,
            attribute_name="device_id",
            attribute_value=str(device.id)
        )
    except KeycloakError as e:
        logger.warning(f"Failed to update Keycloak attribute: {e}")
    
    # Audit log
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        action="device_assigned",
        resource_type="device",
        resource_id=device.id,
        details={
            "device_id": device.device_unique_id,
            "assigned_to_user_id": user.id,
            "assigned_by": current_user.username
        }
    )
    
    logger.info(f"Device {device_id} assigned to user {user.id}")
    return DeviceResponse.model_validate(device)


@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    update_data: DeviceUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update device information (admin only)
    """
    device = await DeviceService.get_device_by_id(db, device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    device = await DeviceService.update_device(db, device, update_data)
    
    # Audit log
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        action="device_updated",
        resource_type="device",
        resource_id=device.id,
        details=update_data.model_dump(exclude_unset=True)
    )
    
    return DeviceResponse.model_validate(device)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete device permanently (admin only)
    """
    device = await DeviceService.get_device_by_id(db, device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Audit log before deletion
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        action="device_deleted",
        resource_type="device",
        resource_id=device.id,
        details={
            "device_id": device.device_unique_id,
            "device_name": device.device_name
        }
    )
    
    await DeviceService.delete_device(db, device)
    
    return None
