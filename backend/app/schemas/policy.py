# schemas/policy.py

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class PolicyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    policy_type: str = Field(..., max_length=50)
    rules: Dict[str, Any]
    priority: int = Field(100, ge=0, le=1000)
    enforce_mode: str = Field("enforce", pattern="^(enforce|monitor|disabled)$")

class PolicyCreate(PolicyBase):
    created_by: Optional[str] = Field(None, max_length=255)

class PolicyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rules: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=0, le=1000)
    is_active: Optional[bool] = None
    enforce_mode: Optional[str] = Field(None, pattern="^(enforce|monitor|disabled)$")
    last_modified_by: Optional[str] = Field(None, max_length=255)

class PolicyResponse(PolicyBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    last_modified_by: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)
