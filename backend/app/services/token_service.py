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
import os

logger = logging.getLogger(__name__)

# For development, we'll use a simple secret key
# In production, this should be stored securely
# Use a fixed secret key so tokens remain valid across restarts
# In production, load this from environment variable or secure storage
TOKEN_SECRET_KEY = os.getenv("DEVICE_TOKEN_SECRET", "ztna-device-token-secret-key-change-in-production-32chars")
TOKEN_ALGORITHM = "HS256"


class TokenService:
    """Service for issuing and managing JWT tokens for device access"""
    
    @staticmethod
    async def issue_device_token(
        db: AsyncSession,
        user: User,
        device: Device,
        resource: str = "*",
        expires_in_minutes: Optional[int] = None,
        user_roles: Optional[list] = None
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
            "user_roles": user_roles or [],  # User roles from Keycloak
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
            # FIRST: Inspect token without any verification to see what's in it
            # This works even if it's a Keycloak token (signed with different key)
            try:
                unverified_payload = jose_jwt.get_unverified_claims(token)
                token_aud = unverified_payload.get('aud')
                token_iss = unverified_payload.get('iss')
                token_type = unverified_payload.get('token_type')
                device_id = unverified_payload.get('device_id')
                
                logger.debug(f"[TOKEN INSPECTION] aud={token_aud}, iss={token_iss}, token_type={token_type}, device_id={device_id}")
                
                # Check if this is a device token
                if token_type != "device_access":
                    logger.warning(f"[TOKEN INSPECTION] Token type mismatch: got '{token_type}', expected 'device_access'. This is a Keycloak token, not a device token!")
                    return None
                
                if token_iss != "ztna-backend":
                    logger.warning(f"[TOKEN INSPECTION] Token issuer mismatch: got '{token_iss}', expected 'ztna-backend'. This is a Keycloak token, not a device token!")
                    return None
                
                if token_aud != "ztna-device-access":
                    logger.warning(f"[TOKEN INSPECTION] Token audience mismatch: got '{token_aud}', expected 'ztna-device-access'")
                    return None
                
                logger.info(f"[TOKEN INSPECTION] Token appears to be a valid device token based on payload")
                
            except Exception as e:
                logger.warning(f"[TOKEN INSPECTION] Could not get unverified claims: {e}")
                return None
            
            # SECOND: Check algorithm
            try:
                unverified_header = jose_jwt.get_unverified_header(token)
                token_alg = unverified_header.get("alg")
                
                if token_alg != TOKEN_ALGORITHM:
                    logger.warning(f"[TOKEN INSPECTION] Token uses algorithm {token_alg}, expected {TOKEN_ALGORITHM}. This might be a Keycloak token.")
                    return None
            except Exception as e:
                logger.warning(f"[TOKEN INSPECTION] Failed to read token header: {e}")
                return None
            
            # Now decode with proper verification (signature, exp, iat)
            # We've already verified audience and issuer above
            try:
                payload = jose_jwt.decode(
                    token,
                    TOKEN_SECRET_KEY,
                    algorithms=[TOKEN_ALGORITHM],
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_iat": True,
                        "verify_aud": False,  # Already verified manually above
                        "verify_iss": False   # Already verified manually above
                    }
                )
                
                logger.info(f"Token verified successfully: aud={payload.get('aud')}, iss={payload.get('iss')}, device_id={payload.get('device_id')}")
            except JWTError as decode_error:
                # Log the full error details
                error_msg = str(decode_error)
                error_type = type(decode_error).__name__
                logger.warning(f"JWT decode error ({error_type}): {error_msg}")
                
                # Try to decode without verification to see what's in the token
                try:
                    # Decode without verification to inspect the payload
                    unverified_payload = jose_jwt.decode(
                        token,
                        TOKEN_SECRET_KEY,
                        algorithms=[TOKEN_ALGORITHM],
                        options={"verify_signature": False, "verify_exp": False, "verify_aud": False, "verify_iss": False}
                    )
                    token_aud = unverified_payload.get('aud')
                    token_iss = unverified_payload.get('iss')
                    token_type = unverified_payload.get('token_type')
                    logger.warning(
                        f"Token inspection: aud={token_aud} (expected=ztna-device-access), "
                        f"iss={token_iss} (expected=ztna-backend), "
                        f"token_type={token_type} (expected=device_access)"
                    )
                    # If this looks like a Keycloak token, provide helpful error
                    if token_type != "device_access" or token_iss != "ztna-backend":
                        logger.warning("This appears to be a Keycloak token, not a device access token!")
                    else:
                        logger.warning("Token appears to be a device token, but verification failed. Check signature/secret key.")
                except Exception as e:
                    logger.warning(f"Could not inspect token: {e}")
                return None
            
            # Verify issuer (audience is already validated by jose_jwt)
            if payload.get("iss") != "ztna-backend":
                logger.warning(f"Token issuer mismatch: got {payload.get('iss')}, expected ztna-backend")
                return None
            
            return payload
            
        except JWTError as e:
            error_type = type(e).__name__
            error_msg = str(e)
            logger.warning(f"JWT error ({error_type}): {error_msg}")
            
            # Try to get more details about the token
            try:
                # Try to decode without any verification to see if it's even a valid JWT
                unverified = jose_jwt.get_unverified_claims(token)
                logger.warning(f"Token is a valid JWT. Contents: aud={unverified.get('aud')}, iss={unverified.get('iss')}, token_type={unverified.get('token_type')}, alg={jose_jwt.get_unverified_header(token).get('alg')}")
            except Exception as inspect_error:
                logger.warning(f"Could not inspect token: {inspect_error}")
            
            return None
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(f"Token verification error ({error_type}): {error_msg}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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

