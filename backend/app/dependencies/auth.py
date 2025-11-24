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
    
    if not token:
        logger.error("No token provided in Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"Received token for verification (length: {len(token)})")
    
    # Verify token with Keycloak using oidc.py
    try:
        token_payload: TokenPayload = verify_jwt_token(token)
        logger.debug(f"Token verified successfully for user: {token_payload.preferred_username}")
    except HTTPException as e:
        logger.warning(f"Token verification failed with HTTPException: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Token verification failed with exception: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get or create user from database
    keycloak_id = token_payload.sub
    
    try:
        # First, try to get user by Keycloak ID
        user = await UserService.get_user_by_keycloak_id(db, keycloak_id)
        
        # If not found, try to get by email (user might exist with different keycloak_id)
        if user is None and token_payload.email:
            user = await UserService.get_user_by_email(db, token_payload.email)
            # If found by email but keycloak_id doesn't match or is None, update it
            if user and (user.keycloak_id != keycloak_id or user.keycloak_id is None):
                logger.info(f"Updating user {user.id} with new Keycloak ID: {keycloak_id} (was: {user.keycloak_id})")
                user.keycloak_id = keycloak_id
                await db.commit()
                await db.refresh(user)
        
        # If still not found, create new user
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
            
            try:
                user = await UserService.create_user(db, user_create)
            except Exception as create_error:
                # If creation fails due to duplicate (race condition), try to fetch again
                error_str = str(create_error).lower()
                if "duplicate" in error_str or "unique" in error_str or "already exists" in error_str:
                    logger.warning(f"User creation failed due to duplicate, retrying fetch: {create_error}")
                    # Try to get by email
                    if token_payload.email:
                        user = await UserService.get_user_by_email(db, token_payload.email)
                    # If still not found, try by keycloak_id again
                    if user is None:
                        user = await UserService.get_user_by_keycloak_id(db, keycloak_id)
                    
                    if user is None:
                        # If still not found, re-raise the original error
                        logger.error(f"Failed to create or find user after duplicate error: {create_error}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to retrieve user information"
                        )
                else:
                    # Re-raise if it's a different error
                    raise
        
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
        logger.error(f"Error getting/creating user: {e}", exc_info=True)
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
