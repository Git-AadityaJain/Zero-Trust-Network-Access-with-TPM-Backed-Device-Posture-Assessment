# models/posture_history.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text, func
from sqlalchemy.orm import relationship
from app.db import Base

class PostureHistory(Base):
    __tablename__ = "posture_history"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Posture check timestamp
    checked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Compliance result
    is_compliant = Column(Boolean, nullable=False)
    compliance_score = Column(Integer, nullable=True)  # 0-100 score
    
    # Detailed posture data
    posture_data = Column(JSON, nullable=False)
    
    # Non-compliance reasons
    violations = Column(JSON, nullable=True)  # List of failed checks
    
    # Signature verification
    signature = Column(Text, nullable=True)
    signature_valid = Column(Boolean, default=True, nullable=False)
    
    # Relationship
    device = relationship("Device", back_populates="posture_history")

    def __repr__(self):
        return f"<PostureHistory(id={self.id}, device_id={self.device_id}, compliant={self.is_compliant}, checked_at={self.checked_at})>"
