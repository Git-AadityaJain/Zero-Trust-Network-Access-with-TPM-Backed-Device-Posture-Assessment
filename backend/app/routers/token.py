# routers/token.py

"""
Token management endpoints
Issues and manages JWT tokens for device access
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db import get_db
from app.services.token_service import TokenService
from app.services.device_service import DeviceService
from app.dependencies.auth import get_current_active_user
from app.models.user import User

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tokens", tags=["tokens"])


# ==================== SCHEMAS ====================

class TokenRequest(BaseModel):
    """Request for device access token"""
    device_id: int = Field(..., description="Device ID to get token for")
    resource: str = Field(default="*", description="Resource being accessed")
    expires_in_minutes: Optional[int] = Field(None, ge=1, le=1440, description="Token expiration in minutes")


class TokenResponse(BaseModel):
    """Response with issued token"""
    token: str
    expires_in_minutes: int
    device_id: int
    device_name: str
    is_compliant: bool
    message: str


class TokenRefreshRequest(BaseModel):
    """Request to refresh a token"""
    token: str = Field(..., description="Current token to refresh")


class TokenVerifyRequest(BaseModel):
    """Request to verify a token"""
    token: str = Field(..., description="Token to verify")


class TokenVerifyResponse(BaseModel):
    """Response from token verification"""
    valid: bool
    payload: Optional[dict] = None
    error: Optional[str] = None


# ==================== ENDPOINTS ====================

@router.post("/issue", response_model=TokenResponse)
async def issue_token(
    request: TokenRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Issue a JWT token for device access after policy evaluation
    
    The token will only be issued if:
    - Device exists and is active
    - User owns the device
    - Policy evaluation allows access
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device is not active or not enrolled"
        )
    
    # Issue token (will evaluate policies)
    token = await TokenService.issue_device_token(
        db=db,
        user=current_user,
        device=device,
        resource=request.resource,
        expires_in_minutes=request.expires_in_minutes
    )
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied by policy evaluation"
        )
    
    expires_in = request.expires_in_minutes or 15
    
    return TokenResponse(
        token=token,
        expires_in_minutes=expires_in,
        device_id=device.id,
        device_name=device.device_name,
        is_compliant=device.is_compliant,
        message="Token issued successfully"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh a device access token (re-evaluates policies)
    """
    # Verify current token
    payload = TokenService.verify_device_token(request.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Get device from token
    device_unique_id = payload.get("device_id")
    if not device_unique_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token does not contain device_id"
        )
    
    device = await DeviceService.get_device_by_unique_id(db, device_unique_id)
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
    
    # Refresh token
    new_token = await TokenService.refresh_device_token(
        db=db,
        token=request.token,
        user=current_user,
        device=device
    )
    
    if not new_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token refresh denied by policy evaluation"
        )
    
    return TokenResponse(
        token=new_token,
        expires_in_minutes=15,
        device_id=device.id,
        device_name=device.device_name,
        is_compliant=device.is_compliant,
        message="Token refreshed successfully"
    )


@router.post("/verify", response_model=TokenVerifyResponse)
async def verify_token(
    request: TokenVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify a device access token (public endpoint for Nginx/gateway)
    """
    payload = TokenService.verify_device_token(request.token)
    
    if not payload:
        return TokenVerifyResponse(
            valid=False,
            error="Invalid or expired token"
        )
    
    return TokenVerifyResponse(
        valid=True,
        payload=payload
    )

