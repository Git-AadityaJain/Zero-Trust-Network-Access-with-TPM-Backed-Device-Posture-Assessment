# models/access_log.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.db import Base

class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Access details
    resource_accessed = Column(String(500), nullable=False)
    access_type = Column(String(50), nullable=False)  # api, network, application
    
    # Access decision
    access_granted = Column(Boolean, nullable=False)
    denial_reason = Column(String(500), nullable=True)
    
    # Policy applied
    policy_id = Column(Integer, nullable=True)
    policy_name = Column(String(255), nullable=True)
    
    # Request metadata
    request_metadata = Column(JSON, nullable=True)
    
    # Network details
    source_ip = Column(String(45), nullable=True)
    destination_ip = Column(String(45), nullable=True)
    
    # Timestamp
    accessed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationship
    device = relationship("Device", back_populates="access_logs")

    def __repr__(self):
        return f"<AccessLog(id={self.id}, device_id={self.device_id}, granted={self.access_granted})>"
