# schemas/enrollment.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class EnrollmentCodeBase(BaseModel):
    description: Optional[str] = Field(None, max_length=500)
    max_uses: int = Field(1, ge=1)
    expires_at: Optional[datetime] = None

class EnrollmentCodeCreate(EnrollmentCodeBase):
    pass

class EnrollmentCodeResponse(EnrollmentCodeBase):
    id: int
    code: str
    current_uses: int
    is_active: bool
    is_expired: bool
    created_at: datetime
    last_used_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)
