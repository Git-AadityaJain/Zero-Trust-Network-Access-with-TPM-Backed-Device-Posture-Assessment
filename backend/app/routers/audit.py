# routers/audit.py

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.audit import AuditLogResponse
from app.services.audit_service import AuditService
from app.dependencies.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get audit logs with filters (admin only in production)
    
    Filters:
    - user_id: Filter by user ID
    - event_type: Filter by event type (e.g., 'login', 'device_enrollment')
    - start_date: Filter logs after this date
    - end_date: Filter logs before this date
    """
    logs = await AuditService.get_audit_logs(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date
    )
    return logs

@router.get("/logs/me", response_model=List[AuditLogResponse])
async def get_my_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs for current user"""
    logs = await AuditService.get_audit_logs(
        db=db,
        skip=skip,
        limit=limit,
        user_id=current_user.id,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date
    )
    return logs

@router.get("/events/types", response_model=List[str])
async def get_event_types(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available event types for filtering"""
    return [
        "login",
        "logout",
        "device_enrollment",
        "device_management",
        "posture_check",
        "policy_management",
        "enrollment_code",
        "access_denied",
        "access_granted"
    ]
