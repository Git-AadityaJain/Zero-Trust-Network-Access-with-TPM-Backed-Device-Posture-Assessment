import requests
from fastapi import Request, HTTPException, status
from jose import jwt
from pydantic import BaseModel, Field
from typing import Union, Optional

class TokenPayload(BaseModel):
    """JWT token payload after validation from Keycloak"""
    # Required fields
    sub: str                                    # User ID (subject)
    exp: int                                    # Token expiration timestamp
    iat: int                                    # Token issued at timestamp
    aud: Union[str, list[str]]                 # Audience (accepts both string and list)
    iss: str                                    # Token issuer
    
    # Optional user info fields
    roles: list[str] = Field(default_factory=list)           # User roles from realm_access
    email: Optional[str] = None                              # User email address
    preferred_username: Optional[str] = None                 # Username
    name: Optional[str] = None                               # Full name
    given_name: Optional[str] = None                         # First name
    family_name: Optional[str] = None                        # Last name
    email_verified: Optional[bool] = False                   # Email verification status
    
    # Device & Posture fields (for future Device Posture Assessment)
    device_id: Optional[str] = None                          # Device identifier
    posture_passed: Optional[bool] = None                    # Device compliance status
    
    class Config:
        populate_by_name = True  # Allow both field names and aliases


# OIDC/Keycloak Configuration
OIDC_ISSUER = "http://ztna-keycloak:8080/realms/ZTNA-Platform"
OIDC_CLIENT_ID = "ztna-backend"
OIDC_JWKS_URI = f"{OIDC_ISSUER}/protocol/openid-connect/certs"

# Cache for OIDC public keys
_oidc_keys = None


def _get_oidc_keys():
    """
    Fetch and cache OIDC public keys from Keycloak.
    Public keys are cached in memory for performance.
    """
    global _oidc_keys
    if _oidc_keys is None:
        try:
            resp = requests.get(OIDC_JWKS_URI, timeout=5)
            resp.raise_for_status()
            _oidc_keys = resp.json()["keys"]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to fetch OIDC keys: {str(e)}"
            )
    return _oidc_keys


def extract_token(request: Request) -> str:
    """
    Extract JWT token from the Authorization header.
    Format: Authorization: Bearer <token>
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing/invalid Authorization header. Use: Authorization: Bearer <token>"
        )
    return auth[7:]  # Remove "Bearer " prefix (7 characters)


def verify_jwt_token(request: Request) -> TokenPayload:
    """
    Verify JWT token signature, expiry, issuer, and audience.
    
    Returns validated TokenPayload with user information and roles.
    
    Raises:
    - 401 Unauthorized: Missing/invalid token or validation failure
    - 503 Service Unavailable: Unable to fetch OIDC keys
    """
    token = extract_token(request)
    
    try:
        # Get key ID from token header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing key ID (kid) in header"
            )
        
        # Find matching public key from Keycloak JWKS
        keys = _get_oidc_keys()
        key = next((k for k in keys if k["kid"] == kid), None)
        
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token key ID not found in JWKS"
            )
        
        # Decode and validate JWT
        # Validates: signature, expiry, audience, issuer
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience="ztna-backend",           # Custom audience for this service
            issuer=OIDC_ISSUER                 # Must match Keycloak issuer
        )
        
        # Extract roles from realm_access claim
        # Structure: { "realm_access": { "roles": ["admin", "user", ...] } }
        roles = []
        realm_access = payload.get("realm_access", {})
        if isinstance(realm_access, dict) and "roles" in realm_access:
            roles = realm_access["roles"]
        
        payload["roles"] = roles
        
        # Create and return TokenPayload with all validated claims
        return TokenPayload(**payload)
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTClaimsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token claims validation failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )
