from fastapi import HTTPException, status, Request
from typing import List
from app.security.oidc import verify_jwt_token, TokenPayload

def require_roles(required_roles: List[str], match_any: bool = False):
    """
    RBAC dependency factory - returns a callable dependency
    
    Args:
        required_roles: List of roles to check
        match_any: If True, user needs ANY role. If False, needs ALL roles.
    """
    async def role_checker(request: Request) -> TokenPayload:
        # Verify JWT first
        current_user = verify_jwt_token(request)
        
        # Check roles
        user_roles = set(current_user.roles)
        required_set = set(required_roles)
        
        if match_any:
            has_access = bool(user_roles & required_set)
        else:
            has_access = required_set.issubset(user_roles)
        
        if not has_access:
            roles_str = " or ".join(required_roles) if match_any else ", ".join(required_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {roles_str}"
            )
        
        return current_user
    
    return role_checker

# Convenience functions - use these directly in endpoints
async def require_admin(request: Request) -> TokenPayload:
    """Require admin role"""
    current_user = verify_jwt_token(request)
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Required role: admin"
        )
    return current_user

async def require_security_analyst(request: Request) -> TokenPayload:
    """Require security-analyst role"""
    current_user = verify_jwt_token(request)
    if "security-analyst" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Required role: security-analyst"
        )
    return current_user

async def require_admin_or_analyst(request: Request) -> TokenPayload:
    """Require admin OR security-analyst role"""
    current_user = verify_jwt_token(request)
    if not any(role in current_user.roles for role in ["admin", "security-analyst"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Required roles: admin or security-analyst"
        )
    return current_user

async def check_device_posture(request: Request) -> TokenPayload:
    """Enforce device posture requirements"""
    current_user = verify_jwt_token(request)
    if not current_user.posture_passed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Device does not meet security posture requirements."
        )
    return current_user
