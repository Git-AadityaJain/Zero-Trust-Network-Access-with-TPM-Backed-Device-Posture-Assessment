# app/routers/user.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    UserWithDevices,
    UserCreateRequest,
    UserUpdateRequest,
    UserPasswordReset,
    UserRoleUpdate,
    UserDetailedResponse,
    UserCreate
)
from app.schemas.device import DeviceResponse
from app.services.user_service import UserService
from app.services.device_service import DeviceService
from app.services.audit_service import AuditService
from app.services.keycloak_service import keycloak_service, KeycloakError, KeycloakUserNotFoundError
from app.dependencies.auth import get_current_active_user
from app.dependencies.rbac import require_role
from app.models.user import User

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


# ==================== CURRENT USER ENDPOINTS ====================

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current authenticated user information"""
    return current_user


@router.get("/me/devices", response_model=UserWithDevices)
async def get_current_user_with_devices(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user with all associated devices"""
    # Eagerly load devices relationship
    result = await db.execute(
        select(User)
        .options(selectinload(User.devices))
        .where(User.id == current_user.id)
    )
    user = result.scalar_one()
    return user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user information (limited fields)"""
    updated_user = await UserService.update_user(db, current_user.id, user_update)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Optionally sync to Keycloak
    try:
        await keycloak_service.update_user(
            user_id=current_user.keycloak_id,
            first_name=user_update.first_name,
            last_name=user_update.last_name
        )
    except KeycloakError as e:
        logger.warning(f"Failed to sync user update to Keycloak: {e}")
    
    return updated_user


# ==================== ADMIN USER MANAGEMENT ENDPOINTS ====================

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user (admin only)
    Creates user in both Keycloak and local database
    
    Workflow:
    1. Create user in Keycloak
    2. Assign roles in Keycloak
    3. Create user in local database
    4. Log audit event
    """
    try:
        # Check if user already exists
        existing_user = await UserService.get_user_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this username already exists"
            )
        
        existing_email = await UserService.get_user_by_email(db, user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        # Step 1: Create user in Keycloak
        logger.info(f"Creating Keycloak user: {user_data.username}")
        
        keycloak_user_id = await keycloak_service.create_user(
            username=user_data.username,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            enabled=True,
            email_verified=False,
            temporary_password=user_data.password if user_data.temporary_password else None
        )
        
        # Set permanent password if not temporary
        if not user_data.temporary_password:
            await keycloak_service.set_user_password(
                user_id=keycloak_user_id,
                password=user_data.password,
                temporary=False
            )
        
        # Step 2: Assign roles in Keycloak
        if user_data.assign_roles:
            await keycloak_service.assign_realm_roles_to_user(
                user_id=keycloak_user_id,
                role_names=user_data.assign_roles
            )
        
        # Step 3: Create user in local database
        user = await UserService.create_user(
            db=db,
            user_data=UserCreate(
                keycloak_id=keycloak_user_id,
                username=user_data.username,
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                is_active=True,
                email_verified=False
            )
        )
        
        # Step 4: Audit log
        await AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action="user_created",
            resource_type="user",
            resource_id=user.id,
            details={
                "username": user.username,
                "email": user.email,
                "keycloak_id": keycloak_user_id,
                "created_by": current_user.username
            }
        )
        
        logger.info(f"User created successfully: {user.username} (ID: {user.id})")
        return user
        
    except KeycloakError as e:
        logger.error(f"Keycloak error during user creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user in Keycloak: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """List all users with pagination (admin only)"""
    users = await UserService.get_all_users(db, skip, limit, active_only)
    return users


@router.get("/{user_id}", response_model=UserDetailedResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user details by ID (admin only)
    Includes Keycloak information (roles, enabled status)
    """
    user = await UserService.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Fetch Keycloak information
    try:
        keycloak_user = await keycloak_service.get_user_by_id(user.keycloak_id)
        keycloak_roles = await keycloak_service.get_user_realm_roles(user.keycloak_id)
        
        user_response = UserDetailedResponse(
            **user.__dict__,
            keycloak_roles=[role["name"] for role in keycloak_roles],
            keycloak_enabled=keycloak_user.get("enabled", True)
        )
        return user_response
        
    except KeycloakError as e:
        logger.warning(f"Failed to fetch Keycloak data for user {user_id}: {e}")
        # Return user without Keycloak data
        return UserDetailedResponse(**user.__dict__)


@router.get("/{user_id}/devices", response_model=List[DeviceResponse])
async def get_user_devices(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """Get all devices for a specific user (admin only)"""
    user = await UserService.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    devices = await DeviceService.get_devices_by_user(db, user_id)
    return devices


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdateRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user information (admin only)
    Updates both Keycloak and local database
    """
    user = await UserService.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Update in Keycloak
        await keycloak_service.update_user(
            user_id=user.keycloak_id,
            email=user_update.email,
            first_name=user_update.first_name,
            last_name=user_update.last_name,
            enabled=user_update.enabled
        )
        
        # Update in local database
        db_update = UserUpdate(
            first_name=user_update.first_name,
            last_name=user_update.last_name,
            is_active=user_update.enabled
        )
        
        updated_user = await UserService.update_user(db, user_id, db_update)
        
        # Update email if changed
        if user_update.email and user_update.email != user.email:
            user.email = user_update.email
            await db.commit()
            await db.refresh(user)
        
        # Audit log
        await AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action="user_updated",
            resource_type="user",
            resource_id=user_id,
            details={
                "updated_by": current_user.username,
                "changes": user_update.model_dump(exclude_unset=True)
            }
        )
        
        logger.info(f"User {user_id} updated by admin {current_user.username}")
        return updated_user
        
    except KeycloakUserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in Keycloak"
        )
    except KeycloakError as e:
        logger.error(f"Keycloak error during user update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user in Keycloak: {str(e)}"
        )


@router.patch("/{user_id}/password", response_model=dict)
async def reset_user_password(
    user_id: int,
    password_data: UserPasswordReset,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """Reset user password (admin only)"""
    user = await UserService.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        await keycloak_service.set_user_password(
            user_id=user.keycloak_id,
            password=password_data.new_password,
            temporary=password_data.temporary
        )
        
        # Audit log
        await AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action="password_reset",
            resource_type="user",
            resource_id=user_id,
            details={
                "reset_by": current_user.username,
                "temporary": password_data.temporary
            }
        )
        
        logger.info(f"Password reset for user {user_id} by admin {current_user.username}")
        return {"message": "Password reset successfully"}
        
    except KeycloakUserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in Keycloak"
        )
    except KeycloakError as e:
        logger.error(f"Keycloak error during password reset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )


@router.patch("/{user_id}/roles", response_model=dict)
async def update_user_roles(
    user_id: int,
    role_data: UserRoleUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """Update user roles in Keycloak (admin only)"""
    user = await UserService.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Get current roles
        current_roles = await keycloak_service.get_user_realm_roles(user.keycloak_id)
        current_role_names = [role["name"] for role in current_roles]
        
        # Remove old roles
        if current_role_names:
            await keycloak_service.remove_realm_roles_from_user(
                user_id=user.keycloak_id,
                role_names=current_role_names
            )
        
        # Assign new roles
        await keycloak_service.assign_realm_roles_to_user(
            user_id=user.keycloak_id,
            role_names=role_data.roles
        )
        
        # Audit log
        await AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action="roles_updated",
            resource_type="user",
            resource_id=user_id,
            details={
                "updated_by": current_user.username,
                "old_roles": current_role_names,
                "new_roles": role_data.roles
            }
        )
        
        logger.info(f"Roles updated for user {user_id} by admin {current_user.username}")
        return {"message": "Roles updated successfully", "roles": role_data.roles}
        
    except KeycloakUserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in Keycloak"
        )
    except KeycloakError as e:
        logger.error(f"Keycloak error during role update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update roles: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user permanently (admin only)
    Deletes from both Keycloak and local database
    """
    user = await UserService.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    try:
        # Audit log before deletion
        await AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action="user_deleted",
            resource_type="user",
            resource_id=user_id,
            details={
                "username": user.username,
                "email": user.email,
                "deleted_by": current_user.username
            }
        )
        
        # Delete from Keycloak
        await keycloak_service.delete_user(user.keycloak_id)
        
        # Delete from local database (cascade will delete related devices)
        await UserService.delete_user(db, user_id)
        
        logger.info(f"User {user_id} deleted by admin {current_user.username}")
        return None
        
    except KeycloakUserNotFoundError:
        # User doesn't exist in Keycloak, just delete from DB
        logger.warning(f"User {user_id} not found in Keycloak, deleting from DB only")
        await UserService.delete_user(db, user_id)
        return None
        
    except KeycloakError as e:
        logger.error(f"Keycloak error during user deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user from Keycloak: {str(e)}"
        )
