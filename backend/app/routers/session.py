# app/routers/session.py

"""
Session management endpoints
Handles single-session-per-user enforcement
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.db import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.keycloak_service import keycloak_service, KeycloakError, KeycloakUserNotFoundError
from app.security.oidc import verify_jwt_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/session", tags=["session"])
security = HTTPBearer()


class SessionInfo(BaseModel):
    """Session information response"""
    user_id: str
    session_count: int
    logged_out_count: int
    message: str


@router.post("/enforce-single", response_model=SessionInfo)
async def enforce_single_session(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Enforce single-session-per-user policy
    Logs out all other sessions for the current user, keeping only the current session
    
    This should be called after successful login to ensure only one active session per user.
    """
    token = credentials.credentials
    
    if not current_user.keycloak_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a Keycloak ID"
        )
    
    try:
        # Extract session ID from token
        token_payload = verify_jwt_token(token)
        session_id = token_payload.sid if hasattr(token_payload, 'sid') else None
        
        # Get all user sessions
        sessions = await keycloak_service.get_user_sessions(current_user.keycloak_id)
        session_count = len(sessions)
        
        if session_count <= 1:
            logger.info(f"User {current_user.keycloak_id} has only one session, no action needed")
            return SessionInfo(
                user_id=current_user.keycloak_id,
                session_count=session_count,
                logged_out_count=0,
                message="User already has only one active session"
            )
        
        # Logout other sessions
        if session_id:
            logged_out_count = await keycloak_service.logout_other_user_sessions(
                current_user.keycloak_id,
                session_id
            )
        else:
            # If we can't identify the current session, logout all and let user re-login
            logger.warning(f"Could not identify current session for user {current_user.keycloak_id}, logging out all sessions")
            await keycloak_service.logout_all_user_sessions(current_user.keycloak_id)
            logged_out_count = session_count
        
        logger.info(
            f"Enforced single session for user {current_user.keycloak_id}: "
            f"logged out {logged_out_count} of {session_count} sessions"
        )
        
        return SessionInfo(
            user_id=current_user.keycloak_id,
            session_count=session_count,
            logged_out_count=logged_out_count,
            message=f"Logged out {logged_out_count} other session(s). Only one session is now active."
        )
        
    except KeycloakUserNotFoundError as e:
        logger.error(f"User not found in Keycloak: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in Keycloak"
        )
    except KeycloakError as e:
        logger.error(f"Keycloak error enforcing single session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enforce single session: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error enforcing single session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enforce single session"
        )


@router.get("/info", response_model=SessionInfo)
async def get_session_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get information about current user's active sessions
    """
    if not current_user.keycloak_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a Keycloak ID"
        )
    
    try:
        sessions = await keycloak_service.get_user_sessions(current_user.keycloak_id)
        session_count = len(sessions)
        
        return SessionInfo(
            user_id=current_user.keycloak_id,
            session_count=session_count,
            logged_out_count=0,
            message=f"User has {session_count} active session(s)"
        )
        
    except KeycloakUserNotFoundError as e:
        logger.error(f"User not found in Keycloak: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in Keycloak"
        )
    except KeycloakError as e:
        logger.error(f"Keycloak error getting session info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session info: {str(e)}"
        )

