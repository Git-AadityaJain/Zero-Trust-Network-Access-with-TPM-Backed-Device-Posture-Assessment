# app/routers/posture.py

from typing import Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db import get_db
from app.services.device_service import DeviceService
from app.services.posture_service import PostureService
from app.services.signature_service import SignatureService
from app.dependencies.auth import get_current_active_user
from app.models.user import User

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/posture", tags=["posture"])


# ==================== SCHEMAS ====================

class PostureSubmission(BaseModel):
    """DPA agent posture submission (public endpoint)"""
    device_id: str = Field(..., description="Device unique ID (UUID)")
    posture_data: Dict[str, Any] = Field(..., description="Complete posture data from DPA")
    signature: str = Field(..., description="TPM/HMAC signature of posture_data")


class PostureSubmissionResponse(BaseModel):
    """Response for posture submission"""
    status: str
    is_compliant: bool
    message: str


# ==================== PUBLIC ENDPOINT (DPA Agent) ====================

@router.post("/submit", response_model=PostureSubmissionResponse)
async def submit_posture(
    submission: PostureSubmission,
    db: AsyncSession = Depends(get_db)
):
    """
    **PUBLIC ENDPOINT**
    Submit device posture data (called by DPA agent)
    No authentication required - validates device_id and signature instead
    """
    try:
        # Get device by unique ID
        device = await DeviceService.get_device_by_unique_id(db, submission.device_id)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Check if device is approved and active
        if device.status != "active" or not device.is_enrolled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Device is not approved or inactive"
            )
        
        # Verify signature
        is_valid_signature = await SignatureService.verify_posture_signature(
            device=device,
            posture_data=submission.posture_data,
            signature=submission.signature
        )
        
        if not is_valid_signature:
            logger.warning(f"Invalid signature for device {submission.device_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
        
        # Evaluate posture compliance
        is_compliant, compliance_score, violations = PostureService.evaluate_compliance(
            posture_data=submission.posture_data
        )
        
        # Update device posture
        await DeviceService.update_device_posture(
            db=db,
            device=device,
            posture_data=submission.posture_data
        )
        
        # Update compliance status
        await DeviceService.update_compliance_status(
            db=db,
            device=device,
            is_compliant=is_compliant
        )
        
        # Handle role revocation/assignment based on compliance (if device has user)
        if device.user_id:
            from app.services.user_service import UserService
            from app.services.policy_service import PolicyService
            from app.services.keycloak_service import keycloak_service
            
            user = await UserService.get_user_by_id(db, device.user_id)
            if user and user.keycloak_id:
                # Get current user roles from Keycloak
                current_roles = await keycloak_service.get_user_realm_roles(user.keycloak_id)
                current_role_names = [role.get("name") for role in current_roles]
                has_dpa_device_role = "dpa-device" in current_role_names
                
                # Revoke dpa-device role if non-compliant
                if not is_compliant and has_dpa_device_role:
                    logger.warning(
                        f"Device {device.id} is non-compliant. Revoking dpa-device role from user {user.id}"
                    )
                    revoked = await keycloak_service.remove_realm_roles_from_user(
                        user_id=user.keycloak_id,
                        role_names=["dpa-device"]
                    )
                    if revoked:
                        logger.info(f"Successfully revoked dpa-device role from user {user.id}")
                    else:
                        logger.error(f"Failed to revoke dpa-device role from user {user.id}")
                
                # Restore dpa-device role if compliant and was previously revoked
                elif is_compliant and not has_dpa_device_role:
                    logger.info(
                        f"Device {device.id} is now compliant. Restoring dpa-device role to user {user.id}"
                    )
                    assigned = await keycloak_service.assign_realm_roles_to_user(
                        user_id=user.keycloak_id,
                        role_names=["dpa-device"]
                    )
                    if assigned:
                        logger.info(f"Successfully restored dpa-device role to user {user.id}")
                    else:
                        logger.error(f"Failed to restore dpa-device role to user {user.id}")
                
                # Re-evaluate policies with updated posture
                allowed, results, denial_reason = await PolicyService.evaluate_policies(
                    db=db,
                    user=user,
                    device=device,
                    posture_data=submission.posture_data,
                    context={"time": datetime.now(timezone.utc).isoformat()}
                )
                
                # Log policy evaluation results
                if not allowed:
                    logger.warning(
                        f"Policy evaluation failed for device {device.id} after posture update: {denial_reason}"
                    )
        
        # Store posture history
        from app.schemas.posture import PostureHistoryCreate
        posture_record = PostureHistoryCreate(
            device_id=device.id,
            posture_data=submission.posture_data,
            is_compliant=is_compliant,
            compliance_score=compliance_score,
            violations=violations,
            signature=submission.signature,
            signature_valid=True
        )
        await PostureService.create_posture_record(db, posture_record)
        
        logger.info(f"Posture submitted for device {submission.device_id}, compliant: {is_compliant}")
        
        return PostureSubmissionResponse(
            status="success",
            is_compliant=is_compliant,
            message="Posture data received and evaluated"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing posture submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process posture submission"
        )


# ==================== ADMIN ENDPOINTS (Authenticated) ====================

@router.get("/device/{device_id}/history")
async def get_device_posture_history(
    device_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get posture history for a device (admin only)"""
    from app.schemas.posture import PostureHistoryResponse
    
    device = await DeviceService.get_device_by_id(db, device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    history = await PostureService.get_posture_history(
        db=db,
        device_id=device_id,
        limit=limit
    )
    
    return [PostureHistoryResponse.model_validate(record) for record in history]


@router.get("/device/{device_id}/latest")
async def get_device_latest_posture(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get latest posture data for a device"""
    device = await DeviceService.get_device_by_id(db, device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return {
        "device_id": device.id,
        "device_unique_id": device.device_unique_id,
        "posture_data": device.posture_data,
        "is_compliant": device.is_compliant,
        "last_posture_check": device.last_posture_check,
        "last_seen_at": device.last_seen_at
    }
