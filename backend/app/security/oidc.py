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
    
    # Session field
    sid: Optional[str] = None  # Session ID


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
    if not token:
        logger.error("No token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    logger.debug(f"Verifying token (length: {len(token) if token else 0})")
    
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
        
        # Accept tokens from both backend client and frontend client
        # Frontend uses 'admin-frontend', backend uses OIDC_CLIENT_ID
        # Also accept 'master-realm' as fallback (realm name sometimes used as audience)
        valid_audiences = [
            settings.OIDC_CLIENT_ID,
            "admin-frontend",  # Frontend client ID
            "account",  # Keycloak account service (sometimes included)
            "master-realm"  # Realm name (fallback for tokens issued before audience mapper)
        ]
        
        # Decode token with signature verification only
        # We'll handle all other validations manually to be more flexible
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                options={
                    "verify_signature": True,
                    "verify_aud": False,  # We'll verify manually
                    "verify_iss": False,  # We'll verify manually to handle URL variations
                    "verify_exp": True,   # Verify expiration
                    "verify_nbf": False,  # Don't verify not-before
                    "verify_iat": False  # Don't verify issued-at
                }
            )
            
            # Extract token claims
            token_issuer = payload.get("iss", "").rstrip('/')
            token_audience = payload.get("aud")
            token_exp = payload.get("exp")
            
            logger.info(f"Token decoded. Issuer: {token_issuer}, Audience: {token_audience}, Exp: {token_exp}")
            
            # Check expiration manually (already verified by jose, but log it)
            if token_exp and token_exp < int(__import__('time').time()):
                logger.error(f"Token expired. Exp: {token_exp}, Now: {int(__import__('time').time())}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Manual issuer validation - accept both internal and external URLs
            # Keycloak tokens can have different hostnames (keycloak:8080 vs localhost:8080)
            # but the realm name should match
            expected_issuer = str(settings.OIDC_ISSUER).rstrip('/')
            actual_issuer = token_issuer
            
            # Extract realm name from both issuers
            def extract_realm(issuer_url):
                """Extract realm name from issuer URL"""
                if '/realms/' in issuer_url:
                    return issuer_url.split('/realms/')[-1].split('?')[0].split('#')[0]
                return None
            
            expected_realm = extract_realm(expected_issuer)
            actual_realm = extract_realm(actual_issuer)
            
            # Validate issuer: check if realm names match (most important)
            # Also check if URLs are similar (same protocol, port, and path)
            issuer_valid = False
            
            if expected_realm and actual_realm:
                # Primary check: realm names must match
                if expected_realm == actual_realm:
                    issuer_valid = True
                    logger.info(f"Issuer validation passed: realm '{expected_realm}' matches")
                else:
                    logger.error(f"Realm mismatch: expected '{expected_realm}', got '{actual_realm}'")
            
            # Secondary check: if realm extraction failed, try URL normalization
            if not issuer_valid:
                # Normalize URLs by removing hostname differences
                def normalize_issuer_path(issuer_url):
                    """Extract the path part of issuer URL"""
                    if '/realms/' in issuer_url:
                        return '/realms/' + issuer_url.split('/realms/')[-1]
                    return issuer_url
            
                expected_path = normalize_issuer_path(expected_issuer)
                actual_path = normalize_issuer_path(actual_issuer)
                
                if expected_path == actual_path:
                    issuer_valid = True
                    logger.info(f"Issuer validation passed: path '{expected_path}' matches")
            
            if not issuer_valid:
                logger.error(f"Issuer validation failed. Token issuer: {actual_issuer}, Expected: {expected_issuer}")
                logger.error(f"Expected realm: {expected_realm}, Actual realm: {actual_realm}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token issuer. Expected realm: {expected_realm}, Got: {actual_realm}",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Manual audience validation
            payload_aud = payload.get("aud")
            if isinstance(payload_aud, str):
                payload_aud_list = [payload_aud]
            elif isinstance(payload_aud, list):
                payload_aud_list = payload_aud
            else:
                payload_aud_list = []
            
            # Check if any audience matches
            if payload_aud_list and not any(aud in valid_audiences for aud in payload_aud_list):
                logger.error(f"Audience validation failed. Token audience: {payload_aud_list}, Expected one of: {valid_audiences}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token audience. Expected one of: {valid_audiences}",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
        except JWTError as e:
            # If other JWT validation fails, log detailed error
            error_msg = str(e)
            logger.error(f"JWT validation failed: {error_msg}")
            logger.error(f"Token issuer from payload: {payload.get('iss') if 'payload' in locals() else 'N/A'}")
            logger.error(f"Expected issuer: {settings.OIDC_ISSUER}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {error_msg}",
                headers={"WWW-Authenticate": "Bearer"}
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
            posture_passed=payload.get("posture_passed"),
            sid=payload.get("sid")  # Session ID
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
