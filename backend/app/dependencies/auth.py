# app/dependencies/auth.py

"""
Authentication dependencies for FastAPI endpoints
Validates JWT tokens and retrieves user from database
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.security.oidc import verify_jwt_token, TokenPayload
from app.services.user_service import UserService
from app.models.user import User
from app.schemas.user import UserCreate

import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validate JWT token using OIDC verification and return current user
    Auto-creates user in database if they exist in Keycloak but not locally
    """
    token = credentials.credentials
    
    # Verify token with Keycloak using oidc.py
    try:
        token_payload: TokenPayload = verify_jwt_token(token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get or create user from database
    keycloak_id = token_payload.sub
    
    try:
        user = await UserService.get_user_by_keycloak_id(db, keycloak_id)
        
        if user is None:
            # Auto-create user from Keycloak token
            logger.info(f"Auto-creating user from Keycloak: {token_payload.preferred_username}")
            
            user_create = UserCreate(
                keycloak_id=keycloak_id,
                username=token_payload.preferred_username or token_payload.email,
                email=token_payload.email or f"{token_payload.preferred_username}@local.dev",
                first_name=token_payload.given_name,
                last_name=token_payload.family_name,
                email_verified=token_payload.email_verified,
                is_active=True
            )
            
            user = await UserService.create_user(db, user_create)
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Update last login timestamp
        await UserService.update_last_login(db, user.id)
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting/creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure user is active (additional check)
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get user if authenticated, otherwise return None
    Useful for optional authentication endpoints
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
