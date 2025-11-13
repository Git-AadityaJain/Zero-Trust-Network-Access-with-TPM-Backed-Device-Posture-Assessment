# schemas/access.py

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class AccessLogBase(BaseModel):
    resource_accessed: str = Field(..., max_length=500)
    access_type: str = Field(..., max_length=50)
    access_granted: bool
    denial_reason: Optional[str] = Field(None, max_length=500)
    policy_id: Optional[int] = None
    policy_name: Optional[str] = Field(None, max_length=255)
    request_metadata: Optional[Dict[str, Any]] = None

class AccessLogCreate(AccessLogBase):
    device_id: int
    source_ip: Optional[str] = Field(None, max_length=45)
    destination_ip: Optional[str] = Field(None, max_length=45)

class AccessLogResponse(AccessLogBase):
    id: int
    device_id: int
    source_ip: Optional[str]
    destination_ip: Optional[str]
    accessed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
