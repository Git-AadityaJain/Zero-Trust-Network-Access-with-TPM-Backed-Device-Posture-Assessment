# routers/enrollment.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.enrollment import EnrollmentCodeCreate, EnrollmentCodeResponse
from app.services.enrollment_service import EnrollmentService
from app.services.audit_service import AuditService
from app.dependencies.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/enrollment", tags=["enrollment"])

@router.post("/codes", response_model=EnrollmentCodeResponse, status_code=status.HTTP_201_CREATED)  # Removed trailing slash
async def create_enrollment_code(
    code_data: EnrollmentCodeCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new enrollment code (admin only in production)"""
    code = await EnrollmentService.create_enrollment_code(db, code_data)
    
    # Log code creation
    await AuditService.log_event(
        db=db,
        user_id=current_user.id,
        event_type="enrollment_code",
        action="create",
        resource_type="enrollment_code",
        resource_id=str(code.id),
        status="success"
    )
    
    return code

@router.get("/codes", response_model=List[EnrollmentCodeResponse])
async def list_enrollment_codes(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all enrollment codes (admin only in production)"""
    codes = await EnrollmentService.get_all_codes(db, skip, limit, active_only)
    return codes

@router.post("/codes/{code_id}/deactivate", response_model=EnrollmentCodeResponse)
async def deactivate_enrollment_code(
    code_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate an enrollment code (admin only in production)"""
    code = await EnrollmentService.deactivate_code(db, code_id)
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment code not found"
        )
    
    # Log deactivation
    await AuditService.log_event(
        db=db,
        user_id=current_user.id,
        event_type="enrollment_code",
        action="deactivate",
        resource_type="enrollment_code",
        resource_id=str(code_id),
        status="success"
    )
    
    return code
