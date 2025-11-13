# models/policy.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, func
from app.db import Base

class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    
    # Policy details
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Policy type
    policy_type = Column(String(50), nullable=False)  # posture, access, network
    
    # Policy rules (JSON format)
    rules = Column(JSON, nullable=False)
    
    # Priority and enforcement
    priority = Column(Integer, default=100, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    enforce_mode = Column(String(20), default="enforce", nullable=False)  # enforce, monitor, disabled
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Metadata
    created_by = Column(String(255), nullable=True)
    last_modified_by = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<Policy(id={self.id}, name={self.name}, type={self.policy_type}, active={self.is_active})>"
