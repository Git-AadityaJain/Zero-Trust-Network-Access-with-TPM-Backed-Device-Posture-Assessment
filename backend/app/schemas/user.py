from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    full_name: str
    username: str
    password: str

class UserOut(BaseModel):
    """Schema for user response"""
    id: int
    email: str
    full_name: str
    username: str
    is_active: bool  # ← ADD THIS

    class Config:
        from_attributes = True
