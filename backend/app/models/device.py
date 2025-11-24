# models/device.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text, func
from sqlalchemy.orm import relationship
from app.db import Base

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # Changed to nullable=True for pending devices
    
    # Device identification
    device_name = Column(String(255), nullable=False)
    device_unique_id = Column(String(512), unique=True, nullable=False, index=True)  # UUID returned to DPA
    
    # 🆕 DPA-specific fields
    fingerprint_hash = Column(String(64), unique=True, nullable=True, index=True)  # SHA256 hardware fingerprint
    enrollment_code_id = Column(Integer, ForeignKey("enrollment_codes.id"), nullable=True)  # Code used for enrollment
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending/active/rejected/inactive
    initial_posture = Column(JSON, nullable=True)  # Posture data submitted during enrollment
    
    # Device information
    os_type = Column(String(50), nullable=True)  # Windows, Linux, macOS
    os_version = Column(String(255), nullable=True)
    device_model = Column(String(255), nullable=True)
    manufacturer = Column(String(255), nullable=True)
    
    # Status flags
    is_enrolled = Column(Boolean, default=False, nullable=False)
    is_compliant = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_posture_check = Column(DateTime(timezone=True), nullable=True)
    
    # Security data
    tpm_public_key = Column(Text, nullable=True)  # PEM-encoded RSA public key from TPM
    attestation_data = Column(JSON, nullable=True)
    
    # Latest posture data (for quick access)
    posture_data = Column(JSON, nullable=True)
    
    # 🆕 Relationships
    user = relationship("User", back_populates="devices")
    posture_history = relationship("PostureHistory", back_populates="device", cascade="all, delete-orphan")
    access_logs = relationship("AccessLog", back_populates="device", cascade="all, delete-orphan")
    enrollment_code = relationship("EnrollmentCode", back_populates="devices")  # NEW
    
    def __repr__(self):
        return f"<Device(id={self.id}, name={self.device_name}, status={self.status})>"
