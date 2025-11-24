# services/token_service.py

"""
JWT Token Service
Issues custom JWT tokens for device access based on policy evaluation
"""

from jose import jwt as jose_jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from app.config import settings
from app.models.device import Device
from app.models.user import User
from app.services.policy_service import PolicyService
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import secrets

logger = logging.getLogger(__name__)

# For development, we'll use a simple secret key
# In production, this should be stored securely
TOKEN_SECRET_KEY = secrets.token_urlsafe(32)
TOKEN_ALGORITHM = "HS256"


class TokenService:
    """Service for issuing and managing JWT tokens for device access"""
    
    @staticmethod
    async def issue_device_token(
        db: AsyncSession,
        user: User,
        device: Device,
        resource: str = "*",
        expires_in_minutes: Optional[int] = None
    ) -> Optional[str]:
        """
        Issue a JWT token for device access after policy evaluation
        
        Args:
            db: Database session
            user: User requesting access
            device: Device to grant access for
            resource: Resource being accessed (default: "*" for all)
            expires_in_minutes: Token expiration time (default: from settings)
        
        Returns:
            JWT token string or None if access denied
        """
        # Evaluate policies first
        allowed, denial_reason, policy_id = await PolicyService.evaluate_for_access(
            db=db,
            user=user,
            device=device,
            resource=resource,
            access_type="read"
        )
        
        if not allowed:
            logger.warning(
                f"Access denied for user {user.id} device {device.id}: {denial_reason}"
            )
            return None
        
        # Get posture data
        posture_data = device.posture_data or {}
        is_compliant = device.is_compliant
        
        # Calculate expiration
        if expires_in_minutes is None:
            expires_in_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=expires_in_minutes)
        
        # Build token payload
        payload = {
            "sub": str(user.id),  # Subject (user ID)
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "device_id": device.device_unique_id,
            "device_name": device.device_name,
            "posture_passed": is_compliant,
            "is_compliant": is_compliant,
            "resource": resource,
            "iat": int(now.timestamp()),  # Issued at
            "exp": int(exp.timestamp()),  # Expiration
            "iss": "ztna-backend",  # Issuer
            "aud": "ztna-device-access",  # Audience
            "token_type": "device_access"
        }
        
        # Add posture data summary to token
        if posture_data:
            payload["posture_summary"] = {
                "antivirus_enabled": posture_data.get("antivirus_enabled", False),
                "firewall_enabled": posture_data.get("firewall_enabled", False),
                "disk_encrypted": posture_data.get("disk_encrypted", False),
            }
        
        # Sign and encode token
        try:
            token = jose_jwt.encode(
                payload,
                TOKEN_SECRET_KEY,
                algorithm=TOKEN_ALGORITHM
            )
            logger.info(
                f"Issued device access token for user {user.id} device {device.id}, expires in {expires_in_minutes} minutes"
            )
            return token
        except Exception as e:
            logger.error(f"Failed to issue token: {e}")
            return None
    
    @staticmethod
    def verify_device_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a device access token
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jose_jwt.decode(
                token,
                TOKEN_SECRET_KEY,
                algorithms=[TOKEN_ALGORITHM],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True
                }
            )
            
            # Verify audience
            if payload.get("aud") != "ztna-device-access":
                logger.warning("Token audience mismatch")
                return None
            
            # Verify issuer
            if payload.get("iss") != "ztna-backend":
                logger.warning("Token issuer mismatch")
                return None
            
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT error: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    @staticmethod
    async def refresh_device_token(
        db: AsyncSession,
        token: str,
        user: User,
        device: Device
    ) -> Optional[str]:
        """
        Refresh a device access token (re-evaluate policies)
        
        Args:
            db: Database session
            token: Current token
            user: User
            device: Device
        
        Returns:
            New token or None if refresh denied
        """
        # Verify current token is valid
        payload = TokenService.verify_device_token(token)
        if not payload:
            return None
        
        # Get resource from original token
        resource = payload.get("resource", "*")
        
        # Issue new token (will re-evaluate policies)
        return await TokenService.issue_device_token(
            db=db,
            user=user,
            device=device,
            resource=resource
        )

