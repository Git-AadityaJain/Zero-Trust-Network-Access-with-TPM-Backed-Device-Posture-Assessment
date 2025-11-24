# schemas/audit.py

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class AuditLogBase(BaseModel):
    event_type: str = Field(..., max_length=100)
    action: str = Field(..., max_length=100)
    resource_type: Optional[str] = Field(None, max_length=100)
    resource_id: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    event_metadata: Optional[Dict[str, Any]] = None
    status: str = Field(..., pattern="^(success|failure|warning)$")

class AuditLogCreate(AuditLogBase):
    user_id: Optional[int] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)

class AuditLogResponse(AuditLogBase):
    id: int
    user_id: Optional[int]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
