# models/audit_log.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, func
from sqlalchemy.orm import relationship
from app.db import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)  # login, device_enroll, policy_change, etc.
    action = Column(String(100), nullable=False)  # create, update, delete, access
    resource_type = Column(String(100), nullable=True)  # device, policy, user
    resource_id = Column(String(100), nullable=True)
    
    # Event description
    description = Column(Text, nullable=True)
    
    # Event metadata
    event_metadata = Column(JSON, nullable=True)
    
    # Request details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Result
    status = Column(String(20), nullable=False)  # success, failure, warning
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationship
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, action={self.action}, status={self.status})>"
