# app/routers/role.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, field_validator

from app.db import get_db
from app.services.keycloak_service import keycloak_service, KeycloakError
from app.services.audit_service import AuditService
from app.dependencies.auth import get_current_active_user
from app.dependencies.rbac import require_role
from app.models.user import User

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/roles", tags=["roles"])


class RoleCreate(BaseModel):
    """Schema for creating a new role"""
    name: str = Field(..., min_length=1, max_length=255, description="Role name (alphanumeric, hyphens, underscores only)")
    description: Optional[str] = Field(None, max_length=255, description="Role description")
    composite: bool = Field(default=False, description="Whether this is a composite role")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate role name format"""
        # Remove leading/trailing whitespace
        v = v.strip()
        
        # Check for empty after trim
        if not v:
            raise ValueError("Role name cannot be empty")
        
        # Keycloak role names should be alphanumeric with hyphens/underscores
        # Spaces are allowed but will be converted to hyphens
        if not v.replace(' ', '').replace('-', '').replace('_', '').isalnum():
            raise ValueError("Role name can only contain letters, numbers, spaces, hyphens, and underscores")
        
        # Convert spaces to hyphens for Keycloak compatibility
        v = v.replace(' ', '-')
        
        return v


class RoleUpdate(BaseModel):
    """Schema for updating a role"""
    description: Optional[str] = Field(None, max_length=255, description="Role description")


class RoleResponse(BaseModel):
    """Role response schema"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    composite: bool = False
    clientRole: bool = False
    containerId: Optional[str] = None


@router.get("", response_model=List[RoleResponse])
async def list_roles(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all realm-level roles (admin only)
    """
    try:
        roles = await keycloak_service.get_realm_roles()
        return [RoleResponse(**role) for role in roles]
    except Exception as e:
        logger.error(f"Error listing roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve roles"
        )


@router.get("/{role_name}", response_model=RoleResponse)
async def get_role(
    role_name: str,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get role details by name (admin only)
    """
    try:
        role = await keycloak_service.get_role_by_name(role_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_name}' not found"
            )
        return RoleResponse(**role)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve role"
        )


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new realm-level role (admin only)
    """
    try:
        # Check if role already exists (case-insensitive check)
        existing_role = await keycloak_service.get_role_by_name(role_data.name)
        if existing_role:
            # If role exists, return it instead of error (idempotent behavior)
            logger.info(f"Role '{role_data.name}' already exists, returning existing role")
            return RoleResponse(**existing_role)
        
        # Create role in Keycloak
        role = await keycloak_service.create_realm_role(
            name=role_data.name,
            description=role_data.description,
            composite=role_data.composite
        )
        
        # Audit log
        await AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action="role_created",
            resource_type="role",
            resource_id=None,
            details={
                "role_name": role_data.name,
                "description": role_data.description,
                "created_by": current_user.username
            }
        )
        
        logger.info(f"Role created: {role_data.name} by {current_user.username}")
        return RoleResponse(**role)
        
    except HTTPException:
        raise
    except KeycloakError as e:
        logger.error(f"Keycloak error creating role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create role: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create role"
        )


@router.put("/{role_name}", response_model=RoleResponse)
async def update_role(
    role_name: str,
    role_update: RoleUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a realm-level role (admin only)
    """
    try:
        # Check if role exists
        existing_role = await keycloak_service.get_role_by_name(role_name)
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_name}' not found"
            )
        
        # Update role in Keycloak
        updated_role = await keycloak_service.update_realm_role(
            role_name=role_name,
            description=role_update.description
        )
        
        # Audit log
        await AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action="role_updated",
            resource_type="role",
            resource_id=None,
            details={
                "role_name": role_name,
                "updated_by": current_user.username
            }
        )
        
        logger.info(f"Role updated: {role_name} by {current_user.username}")
        return RoleResponse(**updated_role)
        
    except HTTPException:
        raise
    except KeycloakError as e:
        logger.error(f"Keycloak error updating role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update role: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error updating role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update role"
        )


@router.delete("/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_name: str,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a realm-level role (admin only)
    Note: Cannot delete default Keycloak roles (admin, default-roles-master, etc.)
    """
    try:
        # Check if role exists
        existing_role = await keycloak_service.get_role_by_name(role_name)
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_name}' not found"
            )
        
        # Prevent deletion of default/system roles
        protected_roles = ["admin", "default-roles-master", "offline_access", "uma_authorization", "create-realm"]
        if role_name in protected_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot delete protected system role '{role_name}'"
            )
        
        # Delete role from Keycloak
        await keycloak_service.delete_realm_role(role_name)
        
        # Audit log
        await AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action="role_deleted",
            resource_type="role",
            resource_id=None,
            details={
                "role_name": role_name,
                "deleted_by": current_user.username
            }
        )
        
        logger.info(f"Role deleted: {role_name} by {current_user.username}")
        
    except HTTPException:
        raise
    except KeycloakError as e:
        logger.error(f"Keycloak error deleting role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete role: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error deleting role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete role"
        )

