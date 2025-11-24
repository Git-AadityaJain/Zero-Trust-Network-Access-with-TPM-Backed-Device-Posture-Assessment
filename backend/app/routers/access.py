# routers/access.py

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db import get_db
from app.schemas.access import AccessLogResponse
from app.services.access_service import AccessService
from app.services.device_service import DeviceService
from app.services.policy_service import PolicyService
from app.security.oidc import verify_jwt_token
from app.dependencies.auth import get_current_active_user
from app.models.user import User

import logging

security = HTTPBearer()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/access", tags=["access"])


# ==================== SCHEMAS ====================

class AccessRequest(BaseModel):
    """Request for resource access"""
    device_id: int = Field(..., description="Device ID requesting access")
    resource: str = Field(..., description="Resource being accessed")
    access_type: str = Field(default="read", description="Type of access: read, write, execute")
    posture_data: Optional[Dict[str, Any]] = Field(None, description="Fresh posture data for this access request")
    posture_signature: Optional[str] = Field(None, description="TPM signature for posture data")


class AccessResponse(BaseModel):
    """Response for access request"""
    allowed: bool
    device_id: int
    resource: str
    reason: Optional[str] = None
    policy_id: Optional[int] = None
    policy_name: Optional[str] = None
    token: Optional[str] = None

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
    return [AccessLogResponse.model_validate(log) for log in logs]

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
    return [AccessLogResponse.model_validate(log) for log in logs]

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
        # Convert to schemas
        all_logs.extend([AccessLogResponse.model_validate(log) for log in logs])
    
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
    return [AccessLogResponse.model_validate(log) for log in logs]


@router.post("/request", response_model=AccessResponse)
async def request_access(
    request: AccessRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    http_request: Request = None
):
    """
    Request access to a resource (integrates policy evaluation)
    
    This endpoint:
    1. Verifies device exists and user owns it
    2. Evaluates all active policies
    3. Grants or denies access based on policy evaluation
    4. Issues JWT token if access granted
    5. Logs the access attempt
    """
    # Get device
    device = await DeviceService.get_device_by_id(db, request.device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Verify user owns the device
    if device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this device"
        )
    
    # Check device is active
    if device.status != "active" or not device.is_enrolled:
        denial_reason = "Device is not active or not enrolled"
        await AccessService.log_access(
            db=db,
            device_id=device.id,
            resource_accessed=request.resource,
            access_type=request.access_type,
            access_granted=False,
            denial_reason=denial_reason,
            source_ip=http_request.client.host if http_request else None
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=denial_reason
        )
    
    # If fresh posture data is provided, submit it as a posture report
    posture_data_to_use = device.posture_data
    if request.posture_data and request.posture_signature:
        try:
            from app.services.signature_service import SignatureService
            from app.services.posture_service import PostureService
            
            # Verify signature
            is_valid_signature = await SignatureService.verify_posture_signature(
                device=device,
                posture_data=request.posture_data,
                signature=request.posture_signature
            )
            
            if is_valid_signature:
                # Evaluate compliance
                is_compliant, compliance_score, violations = PostureService.evaluate_compliance(
                    posture_data=request.posture_data
                )
                
                # Update device posture with fresh data
                await DeviceService.update_device_posture(
                    db=db,
                    device=device,
                    posture_data=request.posture_data
                )
                
                # Update compliance status
                await DeviceService.update_compliance_status(
                    db=db,
                    device=device,
                    is_compliant=is_compliant
                )
                
                # Store posture history
                from app.schemas.posture import PostureHistoryCreate
                posture_record = PostureHistoryCreate(
                    device_id=device.id,
                    posture_data=request.posture_data,
                    is_compliant=is_compliant,
                    compliance_score=compliance_score,
                    violations=violations,
                    signature=request.posture_signature,
                    signature_valid=True
                )
                await PostureService.create_posture_record(db, posture_record)
                
                # Use fresh posture data for policy evaluation
                posture_data_to_use = request.posture_data
                logger.info(f"Fresh posture data submitted and processed for device {device.id} during access request")
            else:
                logger.warning(f"Invalid posture signature for device {device.id} in access request")
                # Continue with stored posture data
        except Exception as e:
            logger.error(f"Error processing fresh posture data in access request: {e}")
            # Continue with stored posture data
    
    # Get user roles from token
    user_roles = []
    try:
        token = credentials.credentials
        token_payload = verify_jwt_token(token)
        user_roles = token_payload.roles or []
    except Exception as e:
        logger.warning(f"Failed to extract roles from token: {e}")
        user_roles = []
    
    # Evaluate policies with user roles in context
    context = {
        "user_roles": user_roles,
        "time": datetime.now(timezone.utc).isoformat()
    }
    
    allowed, results, denial_reason = await PolicyService.evaluate_policies(
        db=db,
        user=current_user,
        device=device,
        posture_data=posture_data_to_use,  # Use fresh posture if provided, otherwise stored
        context=context
    )
    
    # Find the policy that denied if any
    policy_id = None
    policy_name = None
    if not allowed:
        for result in results:
            if not result.allowed and result.policy_id:
                policy_id = result.policy_id
                policy_name = result.policy_name
                break
    
    # Get policy name if policy denied
    policy_name = None
    if policy_id:
        policy = await PolicyService.get_policy_by_id(db, policy_id)
        if policy:
            policy_name = policy.name
    
    # Log access attempt
    await AccessService.log_access(
        db=db,
        device_id=device.id,
        resource_accessed=request.resource,
        access_type=request.access_type,
        access_granted=allowed,
        denial_reason=denial_reason,
        policy_id=policy_id,
        policy_name=policy_name,
        source_ip=http_request.client.host if http_request else None
    )
    
    if not allowed:
        logger.warning(
            f"Access denied for user {current_user.id} device {device.id} to {request.resource}: {denial_reason}"
        )
        return AccessResponse(
            allowed=False,
            device_id=device.id,
            resource=request.resource,
            reason=denial_reason,
            policy_id=policy_id,
            policy_name=policy_name
        )
    
    # Issue token if access granted
    from app.services.token_service import TokenService
    token = await TokenService.issue_device_token(
        db=db,
        user=current_user,
        device=device,
        resource=request.resource
    )
    
    logger.info(
        f"Access granted for user {current_user.id} device {device.id} to {request.resource}"
    )
    
    return AccessResponse(
        allowed=True,
        device_id=device.id,
        resource=request.resource,
        reason="Access granted by policy evaluation",
        token=token
    )
