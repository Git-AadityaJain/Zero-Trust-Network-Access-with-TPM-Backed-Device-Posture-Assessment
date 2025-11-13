# routers/access.py

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.access import AccessLogResponse
from app.services.access_service import AccessService
from app.services.device_service import DeviceService
from app.dependencies.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/access", tags=["access"])

@router.get("/logs", response_model=List[AccessLogResponse])
async def get_access_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    device_id: Optional[int] = Query(None),
    access_granted: Optional[bool] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get access logs with filters (admin only in production)
    
    Filters:
    - device_id: Filter by device ID
    - access_granted: Filter by access result (true/false)
    - start_date: Filter logs after this date
    - end_date: Filter logs before this date
    """
    logs = await AccessService.get_access_logs(
        db=db,
        skip=skip,
        limit=limit,
        device_id=device_id,
        access_granted=access_granted,
        start_date=start_date,
        end_date=end_date
    )
    return logs

@router.get("/device/{device_id}", response_model=List[AccessLogResponse])
async def get_device_access_logs(
    device_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    access_granted: Optional[bool] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get access logs for a specific device"""
    
    # Verify device exists and user owns it
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
    
    logs = await AccessService.get_access_logs(
        db=db,
        skip=skip,
        limit=limit,
        device_id=device_id,
        access_granted=access_granted,
        start_date=start_date,
        end_date=end_date
    )
    return logs

@router.get("/me/devices", response_model=List[AccessLogResponse])
async def get_my_devices_access_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    access_granted: Optional[bool] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get access logs for all devices owned by current user"""
    
    # Get all user devices
    devices = await DeviceService.get_devices_by_user(db, current_user.id)
    device_ids = [device.id for device in devices]
    
    if not device_ids:
        return []
    
    # Get access logs for all user devices
    all_logs = []
    for device_id in device_ids:
        logs = await AccessService.get_access_logs(
            db=db,
            skip=0,
            limit=limit,
            device_id=device_id,
            access_granted=access_granted,
            start_date=start_date,
            end_date=end_date
        )
        all_logs.extend(logs)
    
    # Sort by accessed_at descending and apply pagination
    all_logs.sort(key=lambda x: x.accessed_at, reverse=True)
    return all_logs[skip:skip + limit]

@router.get("/denied", response_model=List[AccessLogResponse])
async def get_denied_access_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all denied access attempts (admin only in production)"""
    logs = await AccessService.get_access_logs(
        db=db,
        skip=skip,
        limit=limit,
        access_granted=False,
        start_date=start_date,
        end_date=end_date
    )
    return logs
