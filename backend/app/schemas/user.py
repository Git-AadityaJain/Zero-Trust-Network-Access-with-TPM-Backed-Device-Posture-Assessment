# schemas/user.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from .device import DeviceResponse
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)

class UserCreate(UserBase):
    keycloak_id: str = Field(..., max_length=255)
    email_verified: bool = False
    is_active: bool = True

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    email_verified: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    keycloak_id: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)

class UserWithDevices(UserResponse):
    devices: List["DeviceResponse"] = []
    
    model_config = ConfigDict(from_attributes=True)
