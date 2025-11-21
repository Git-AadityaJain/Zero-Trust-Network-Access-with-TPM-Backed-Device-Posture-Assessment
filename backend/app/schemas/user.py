# app/schemas/user.py

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict

if TYPE_CHECKING:
    from app.schemas.device import DeviceResponse
class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    """Schema for creating user in DB (after Keycloak creation)"""
    keycloak_id: str = Field(..., max_length=255)
    email_verified: bool = False
    is_active: bool = True


class UserCreateRequest(UserBase):
    """Admin request to create a new user (creates in both Keycloak and DB)"""
    password: str = Field(..., min_length=8, description="Initial password (temporary)")
    temporary_password: bool = Field(default=True, description="User must change password on first login")
    assign_roles: Optional[List[str]] = Field(default=["user"], description="Roles to assign in Keycloak")


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    email_verified: Optional[bool] = None


class UserUpdateRequest(BaseModel):
    """Admin request to update user (syncs to both Keycloak and DB)"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    enabled: Optional[bool] = None  # Keycloak enabled status


class UserPasswordReset(BaseModel):
    """Request to reset user password"""
    new_password: str = Field(..., min_length=8)
    temporary: bool = Field(default=True, description="User must change password on next login")


class UserRoleUpdate(BaseModel):
    """Request to update user roles"""
    roles: List[str] = Field(..., min_length=1, description="List of role names to assign")


class UserResponse(UserBase):
    """User response with full details"""
    id: int
    keycloak_id: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class UserWithDevices(UserResponse):
    """User response with associated devices"""
    devices: List[Any] = Field(default_factory=list, description="List of device objects")
    
    model_config = ConfigDict(from_attributes=True)


class UserDetailedResponse(UserResponse):
    """User with additional Keycloak information"""
    keycloak_roles: List[str] = Field(default_factory=list)
    keycloak_enabled: bool = True
