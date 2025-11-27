# routers/token.py

"""
Token management endpoints
Issues and manages JWT tokens for device access
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db import get_db
from app.services.token_service import TokenService
from app.services.device_service import DeviceService
from app.services.challenge_service import ChallengeService
from app.services.signature_service import SignatureService
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.security.oidc import verify_jwt_token

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tokens", tags=["tokens"])


# ==================== SCHEMAS ====================

class ChallengeRequest(BaseModel):
    """Request for a TPM attestation challenge"""
    device_id: int = Field(..., description="Device ID to get challenge for")


class ChallengeResponse(BaseModel):
    """Response with challenge for TPM signing"""
    challenge: str
    expires_in_seconds: int
    message: str


class TokenRequest(BaseModel):
    """Request for device access token (requires TPM-signed challenge)"""
    device_id: int = Field(..., description="Device ID to get token for")
    challenge: str = Field(..., description="Challenge string received from /challenge endpoint")
    challenge_signature: str = Field(..., description="TPM signature of the challenge (base64-encoded)")
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

@router.post("/challenge", response_model=ChallengeResponse)
async def get_challenge(
    request: ChallengeRequest,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a challenge (nonce) for TPM-based device attestation
    
    This challenge must be signed by the device's TPM before requesting a token.
    This ensures that only the genuine enrolled device can obtain access tokens,
    preventing stolen credentials from being used.
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
    
    # Check device is enrolled and has TPM key
    if not device.is_enrolled or device.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device is not enrolled or not active"
        )
    
    if not device.tpm_public_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device does not have a TPM public key. Device attestation is required."
        )
    
    # Generate challenge
    challenge = ChallengeService.generate_challenge(device.device_unique_id)
    
    return ChallengeResponse(
        challenge=challenge,
        expires_in_seconds=ChallengeService.CHALLENGE_EXPIRY_SECONDS,
        message="Challenge generated. Sign this challenge with your device's TPM before requesting a token."
    )


@router.post("/issue", response_model=TokenResponse)
async def issue_token(
    request: TokenRequest,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Issue a JWT token for device access after TPM attestation and policy evaluation
    
    The token will only be issued if:
    - Device exists and is active
    - User owns the device
    - Challenge is valid and signed by device's TPM (proves genuine device)
    - Policy evaluation allows access
    
    This prevents stolen credentials from being used, as the attacker would need
    the physical device and its TPM to sign the challenge.
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
    
    # Verify challenge is valid
    if not ChallengeService.verify_challenge(request.challenge, device.device_unique_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired challenge. Please request a new challenge."
        )
    
    # Verify TPM signature on challenge
    if not device.tpm_public_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device does not have a TPM public key. Device attestation is required."
        )
    
    is_valid_signature = await SignatureService.verify_challenge_signature(
        device=device,
        challenge=request.challenge,
        signature=request.challenge_signature
    )
    
    if not is_valid_signature:
        logger.warning(
            f"Invalid TPM signature for challenge from device {device.device_unique_id}. "
            f"This may indicate an attempt to use stolen credentials."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid TPM signature. The challenge must be signed by the device's TPM."
        )
    
    # Challenge verified - mark as consumed
    ChallengeService.consume_challenge(request.challenge)
    
    # Get user roles from the current request token
    token_payload = verify_jwt_token(credentials.credentials)
    user_roles = token_payload.roles or []
    
    # Issue token (will evaluate policies)
    token = await TokenService.issue_device_token(
        db=db,
        user=current_user,
        device=device,
        resource=request.resource,
        expires_in_minutes=request.expires_in_minutes,
        user_roles=user_roles
    )
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied by policy evaluation"
        )
    
    expires_in = request.expires_in_minutes or 15
    
    logger.info(
        f"Token issued successfully for device {device.device_unique_id} "
        f"after TPM attestation verification"
    )
    
    return TokenResponse(
        token=token,
        expires_in_minutes=expires_in,
        device_id=device.id,
        device_name=device.device_name,
        is_compliant=device.is_compliant,
        message="Token issued successfully after device attestation"
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

