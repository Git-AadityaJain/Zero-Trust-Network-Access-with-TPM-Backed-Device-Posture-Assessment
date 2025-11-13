# models/enrollment_code.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from app.db import Base

class EnrollmentCode(Base):
    __tablename__ = "enrollment_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(255), unique=True, nullable=False, index=True)
    
    # Usage tracking
    max_uses = Column(Integer, default=1, nullable=False)
    current_uses = Column(Integer, default=0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Metadata
    description = Column(String(500), nullable=True)
    created_by = Column(Integer, nullable=True)  # Admin user ID who created it
    
    # 🆕 Relationship to devices
    devices = relationship("Device", back_populates="enrollment_code")  # NEW
    
    def __repr__(self):
        return f"<EnrollmentCode(code={self.code}, uses={self.current_uses}/{self.max_uses})>"
