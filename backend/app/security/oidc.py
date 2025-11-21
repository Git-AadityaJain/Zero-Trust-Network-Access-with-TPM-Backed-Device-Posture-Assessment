# app/security/oidc.py

import requests
from fastapi import HTTPException, status
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from typing import Union, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Cache for JWKS keys
_jwks_cache = None


class TokenPayload(BaseModel):
    """JWT token payload after validation from Keycloak"""
    # Required fields
    sub: str  # User ID (subject)
    exp: int  # Token expiration timestamp
    iat: int  # Token issued at timestamp
    aud: Union[str, list[str]]  # Audience
    iss: str  # Token issuer
    
    # Optional user info fields
    roles: list[str] = Field(default_factory=list)
    email: Optional[str] = None
    preferred_username: Optional[str] = None
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email_verified: Optional[bool] = False
    
    # Device & Posture fields
    device_id: Optional[str] = None
    posture_passed: Optional[bool] = None


def get_jwks():
    """Fetch and cache JWKS from Keycloak"""
    global _jwks_cache
    
    if _jwks_cache is not None:
        return _jwks_cache
    
    try:
        response = requests.get(str(settings.OIDC_JWKS_URI), timeout=10)
        response.raise_for_status()
        _jwks_cache = response.json()
        logger.info("JWKS fetched and cached successfully")
        return _jwks_cache
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch public keys"
        )


def verify_jwt_token(token: str) -> TokenPayload:
    """
    Verify JWT token with Keycloak and return payload
    
    Args:
        token: JWT token string
    
    Returns:
        TokenPayload with user information
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Get JWKS
        jwks = get_jwks()
        
        # Decode and verify token
        unverified_header = jwt.get_unverified_header(token)
        
        # Find the matching key
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find matching key"
            )
        
        # Verify and decode
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=settings.OIDC_CLIENT_ID,
            issuer=str(settings.OIDC_ISSUER),
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True
            }
        )
        
        # Extract roles from realm_access
        roles = payload.get("realm_access", {}).get("roles", [])
        
        # Build TokenPayload
        token_data = TokenPayload(
            sub=payload["sub"],
            exp=payload["exp"],
            iat=payload["iat"],
            aud=payload["aud"],
            iss=payload["iss"],
            roles=roles,
            email=payload.get("email"),
            preferred_username=payload.get("preferred_username"),
            name=payload.get("name"),
            given_name=payload.get("given_name"),
            family_name=payload.get("family_name"),
            email_verified=payload.get("email_verified", False),
            device_id=payload.get("device_id"),
            posture_passed=payload.get("posture_passed")
        )
        
        return token_data
        
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )
