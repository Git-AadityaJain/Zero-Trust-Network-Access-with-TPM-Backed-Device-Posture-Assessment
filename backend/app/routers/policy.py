# routers/policy.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.policy import PolicyCreate, PolicyUpdate, PolicyResponse
from app.services.policy_service import PolicyService
from app.services.audit_service import AuditService
from app.dependencies.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/policies", tags=["policies"])

@router.post("/", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy_data: PolicyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new policy (admin only in production)"""
    
    # Check if policy with same name exists
    existing_policy = await PolicyService.get_policy_by_name(db, policy_data.name)
    if existing_policy:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Policy with this name already exists"
        )
    
    policy = await PolicyService.create_policy(db, policy_data)
    
    # Log policy creation
    await AuditService.log_event(
        db=db,
        user_id=current_user.id,
        event_type="policy_management",
        action="create",
        resource_type="policy",
        resource_id=str(policy.id),
        status="success",
        description=f"Created policy: {policy.name}"
    )
    
    return policy

@router.get("", response_model=List[PolicyResponse])  # Changed from "/" to ""
async def list_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(False),
    policy_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all policies with optional filters"""
    policies = await PolicyService.get_all_policies(
        db, skip, limit, active_only, policy_type
    )
    return policies

@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get policy by ID"""
    policy = await PolicyService.get_policy_by_id(db, policy_id)
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    return policy

@router.patch("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: int,
    policy_update: PolicyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a policy (admin only in production)"""
    policy = await PolicyService.get_policy_by_id(db, policy_id)
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    # FIXED: Create a new update dict with last_modified_by
    update_dict = policy_update.model_dump(exclude_unset=True)
    update_dict['last_modified_by'] = current_user.username
    
    # Create new PolicyUpdate instance
    final_update = PolicyUpdate(**update_dict)
    
    updated_policy = await PolicyService.update_policy(db, policy_id, final_update)
    
    # Log policy update
    await AuditService.log_event(
        db=db,
        user_id=current_user.id,
        event_type="policy_management",
        action="update",
        resource_type="policy",
        resource_id=str(policy_id),
        status="success",
        description=f"Updated policy: {updated_policy.name}"
    )
    
    return updated_policy

@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a policy (admin only in production)"""
    policy = await PolicyService.get_policy_by_id(db, policy_id)
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    policy_name = policy.name  # Store before deletion
    
    success = await PolicyService.delete_policy(db, policy_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete policy"
        )
    
    # Log policy deletion
    await AuditService.log_event(
        db=db,
        user_id=current_user.id,
        event_type="policy_management",
        action="delete",
        resource_type="policy",
        resource_id=str(policy_id),
        status="success",
        description=f"Deleted policy: {policy_name}"
    )

@router.post("/{policy_id}/activate", response_model=PolicyResponse)
async def activate_policy(
    policy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Activate a policy"""
    policy = await PolicyService.get_policy_by_id(db, policy_id)
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    policy_update = PolicyUpdate(is_active=True, last_modified_by=current_user.username)
    updated_policy = await PolicyService.update_policy(db, policy_id, policy_update)
    
    # Log activation
    await AuditService.log_event(
        db=db,
        user_id=current_user.id,
        event_type="policy_management",
        action="activate",
        resource_type="policy",
        resource_id=str(policy_id),
        status="success"
    )
    
    return updated_policy

@router.post("/{policy_id}/deactivate", response_model=PolicyResponse)
async def deactivate_policy(
    policy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a policy"""
    policy = await PolicyService.get_policy_by_id(db, policy_id)
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    policy_update = PolicyUpdate(is_active=False, last_modified_by=current_user.username)
    updated_policy = await PolicyService.update_policy(db, policy_id, policy_update)
    
    # Log deactivation
    await AuditService.log_event(
        db=db,
        user_id=current_user.id,
        event_type="policy_management",
        action="deactivate",
        resource_type="policy",
        resource_id=str(policy_id),
        status="success"
    )
    
    return updated_policy
