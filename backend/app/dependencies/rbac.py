# app/dependencies/rbac.py

"""
Role-Based Access Control (RBAC) dependencies
Checks user roles from Keycloak tokens
"""

from typing import List, Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.security.oidc import verify_jwt_token, TokenPayload
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


def require_role(role: str) -> Callable:
    """
    Dependency factory that requires a specific role
    
    Usage:
        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
        async def admin_endpoint():
            ...
    
    Or:
        @router.get("/admin")
        async def admin_endpoint(current_user: User = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        # Get current user (validates token and gets user from DB)
        user = await get_current_user(credentials, db)
        
        # Verify token to get roles
        token_payload: TokenPayload = verify_jwt_token(credentials.credentials)
        
        # Check if user has required role
        if role not in token_payload.roles:
            logger.warning(
                f"User {user.username} attempted to access endpoint requiring role '{role}'. "
                f"User roles: {token_payload.roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {role}"
            )
        
        return user
    
    return role_checker


def require_any_role(*roles: str) -> Callable:
    """
    Dependency factory that requires ANY of the specified roles
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(current_user: User = Depends(require_any_role("admin", "editor"))):
            ...
    """
    async def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        user = await get_current_user(credentials, db)
        token_payload: TokenPayload = verify_jwt_token(credentials.credentials)
        
        # Check if user has any of the required roles
        user_roles = set(token_payload.roles)
        required_roles = set(roles)
        
        if not user_roles.intersection(required_roles):
            logger.warning(
                f"User {user.username} attempted to access endpoint requiring any of {roles}. "
                f"User roles: {token_payload.roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role (any): {', '.join(roles)}"
            )
        
        return user
    
    return role_checker


def require_all_roles(*roles: str) -> Callable:
    """
    Dependency factory that requires ALL of the specified roles
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(current_user: User = Depends(require_all_roles("admin", "superuser"))):
            ...
    """
    async def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        user = await get_current_user(credentials, db)
        token_payload: TokenPayload = verify_jwt_token(credentials.credentials)
        
        # Check if user has all required roles
        user_roles = set(token_payload.roles)
        required_roles = set(roles)
        
        if not required_roles.issubset(user_roles):
            missing_roles = required_roles - user_roles
            logger.warning(
                f"User {user.username} attempted to access endpoint requiring all of {roles}. "
                f"Missing roles: {missing_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles (all): {', '.join(roles)}"
            )
        
        return user
    
    return role_checker


# Convenience dependencies for common roles
require_admin = require_role("admin")
require_security_analyst = require_role("security-analyst")
require_dpa_device = require_role("dpa-device")
require_admin_or_analyst = require_any_role("admin", "security-analyst")
