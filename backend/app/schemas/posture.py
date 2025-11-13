# schemas/posture.py

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

class PostureHistoryBase(BaseModel):
    is_compliant: bool
    compliance_score: Optional[int] = Field(None, ge=0, le=100)
    posture_data: Dict[str, Any]
    violations: Optional[List[str]] = None

class PostureHistoryCreate(PostureHistoryBase):
    device_id: int
    signature: Optional[str] = None
    signature_valid: bool = True

class PostureHistoryResponse(PostureHistoryBase):
    id: int
    device_id: int
    checked_at: datetime
    signature_valid: bool
    
    model_config = ConfigDict(from_attributes=True)

class PostureSubmission(BaseModel):
    device_unique_id: str = Field(..., max_length=512)
    posture_data: Dict[str, Any]
    signature: str
