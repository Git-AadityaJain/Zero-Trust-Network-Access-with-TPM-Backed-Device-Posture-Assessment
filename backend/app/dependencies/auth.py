# dependencies/auth.py

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.db import get_db
from app.services.user_service import UserService
from app.models.user import User
from app.schemas.user import UserCreate

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validate JWT token and return current user
    """
    token = credentials.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token WITHOUT signature verification
        # Note: key parameter is required but empty since verify_signature=False
        payload = jwt.decode(
            token,
            key="",  # Empty key - not used since verify_signature=False
            options={
                "verify_signature": False,
                "verify_aud": False,
                "verify_iss": False,
                "verify_exp": False
            }
        )
        
        # Extract user info from token
        keycloak_id: str = payload.get("sub")
        username: str = payload.get("preferred_username")
        email: str = payload.get("email")
        email_verified: bool = payload.get("email_verified", False)
        given_name: str = payload.get("given_name", "")
        family_name: str = payload.get("family_name", "")
        
        # Provide default email if missing
        if not email:
            email = f"{username}@local.dev"
        
        if keycloak_id is None or username is None:
            raise credentials_exception
            
    except JWTError as e:
        print(f"JWT Error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise credentials_exception
    
    try:
        # Get or create user from database
        user = await UserService.get_user_by_keycloak_id(db, keycloak_id)
        
        if user is None:
            # Auto-create user from Keycloak token
            print(f"Creating new user from Keycloak: {username}")
            user_create = UserCreate(
                keycloak_id=keycloak_id,
                username=username,
                email=email,
                first_name=given_name,
                last_name=family_name,
                email_verified=email_verified,
                is_active=True
            )
            user = await UserService.create_user(db, user_create)
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        # Update last login
        await UserService.update_last_login(db, user.id)
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting/creating user: {str(e)}")
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user is active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get user if authenticated, otherwise None"""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
