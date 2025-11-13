# routers/posture.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.posture import PostureSubmission, PostureHistoryResponse, PostureHistoryCreate
from app.services.posture_service import PostureService
from app.services.device_service import DeviceService
from app.services.audit_service import AuditService
from app.dependencies.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/posture", tags=["posture"])

@router.post("/submit", response_model=PostureHistoryResponse, status_code=status.HTTP_201_CREATED)
async def submit_posture_data(
    posture_data: PostureSubmission,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit device posture data for compliance check"""
    
    # Get device
    device = await DeviceService.get_device_by_unique_id(db, posture_data.device_unique_id)
    
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
    
    # Evaluate compliance
    is_compliant, score, violations = await PostureService.evaluate_compliance(
        posture_data.posture_data
    )
    
    # Create posture history record
    posture_create = PostureHistoryCreate(
        device_id=device.id,
        is_compliant=is_compliant,
        compliance_score=score,
        posture_data=posture_data.posture_data,
        violations=violations,
        signature=posture_data.signature,
        signature_valid=True  # TODO: Verify signature with TPM public key
    )
    
    posture_record = await PostureService.create_posture_record(db, posture_create)
    
    # Update device compliance status
    await DeviceService.update_compliance_status(
        db, device.id, is_compliant, posture_data.posture_data
    )
    
    # Log posture submission
    await AuditService.log_event(
        db=db,
        user_id=current_user.id,
        event_type="posture_check",
        action="submit",
        resource_type="device",
        resource_id=str(device.id),
        status="success" if is_compliant else "warning",
        description=f"Compliance: {is_compliant}, Score: {score}"
    )
    
    return posture_record

@router.get("/device/{device_id}/history", response_model=List[PostureHistoryResponse])
async def get_posture_history(
    device_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get posture history for a device"""
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
    
    history = await PostureService.get_posture_history(db, device_id, skip, limit)
    return history

@router.get("/device/{device_id}/latest", response_model=PostureHistoryResponse)
async def get_latest_posture(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the latest posture check for a device"""
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
    
    latest_posture = await PostureService.get_latest_posture(db, device_id)
    
    if not latest_posture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No posture data available"
        )
    
    return latest_posture
