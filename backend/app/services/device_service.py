# app/services/device_service.py

from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.device import Device
from app.models.user import User
from app.schemas.device import DeviceEnrollmentRequest, DeviceUpdate
from datetime import datetime, timezone
import uuid
import logging
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class DeviceService:
    """Service for device management operations"""
    
    @staticmethod
    def _convert_public_key_to_pem(public_key_data: str) -> str:
        """
        Convert public key from base64 SPKI format to PEM format
        TPMSigner returns base64-encoded SubjectPublicKeyInfo, but backend needs PEM
        """
        try:
            # Try to decode as base64 first
            try:
                key_bytes = base64.b64decode(public_key_data)
            except Exception:
                # If it's already PEM format, return as-is
                if public_key_data.strip().startswith("-----BEGIN"):
                    return public_key_data.strip()
                raise ValueError("Invalid public key format")
            
            # Load as DER (SPKI format)
            try:
                public_key = serialization.load_der_public_key(
                    key_bytes,
                    backend=default_backend()
                )
            except Exception:
                # Try PEM format
                public_key = serialization.load_pem_public_key(
                    public_key_data.encode(),
                    backend=default_backend()
                )
                return public_key_data.strip()
            
            # Convert to PEM format
            pem_key = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pem_key.decode('utf-8').strip()
        except Exception as e:
            logger.warning(f"Failed to convert public key to PEM: {e}. Storing as-is.")
            return public_key_data.strip()
    
    @staticmethod
    async def enroll_device(
        db: AsyncSession,
        enrollment_data: DeviceEnrollmentRequest,
        enrollment_code_id: int
    ) -> Device:
        """
        Enroll a new device (called by DPA agent without authentication)
        Creates device in 'pending' status awaiting admin approval
        """
        # Generate unique device ID (UUID)
        device_unique_id = str(uuid.uuid4())
        
        # Convert public key to PEM format if needed
        tpm_public_key_pem = DeviceService._convert_public_key_to_pem(
            enrollment_data.tpm_public_key
        )
        
        # Create device with pending status
        device = Device(
            device_unique_id=device_unique_id,
            device_name=enrollment_data.device_name,
            fingerprint_hash=enrollment_data.fingerprint_hash,
            tpm_public_key=tpm_public_key_pem,
            os_type=enrollment_data.os_type,
            os_version=enrollment_data.os_version,
            device_model=enrollment_data.device_model,
            manufacturer=enrollment_data.manufacturer,
            initial_posture=enrollment_data.initial_posture,
            enrollment_code_id=enrollment_code_id,
            status="pending",  # Awaiting admin approval
            is_enrolled=False,  # Not fully enrolled until approved
            is_compliant=False,
            is_active=True,
            user_id=None  # Will be set on approval
        )
        
        db.add(device)
        await db.commit()
        await db.refresh(device)
        
        logger.info(f"Device enrolled with pending status: {device_unique_id}")
        return device
    
    @staticmethod
    async def get_device_by_id(db: AsyncSession, device_id: int) -> Optional[Device]:
        """Get device by ID"""
        result = await db.execute(
            select(Device)
            .options(selectinload(Device.user))
            .where(Device.id == device_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_device_by_unique_id(db: AsyncSession, device_unique_id: str) -> Optional[Device]:
        """Get device by unique ID (UUID)"""
        result = await db.execute(
            select(Device)
            .options(selectinload(Device.user))
            .where(Device.device_unique_id == device_unique_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_device_by_fingerprint(db: AsyncSession, fingerprint_hash: str) -> Optional[Device]:
        """Get device by hardware fingerprint"""
        result = await db.execute(
            select(Device).where(Device.fingerprint_hash == fingerprint_hash)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_devices_by_status(
        db: AsyncSession,
        status: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Device]:
        """Get devices filtered by status"""
        result = await db.execute(
            select(Device)
            .options(selectinload(Device.user))
            .where(Device.status == status)
            .order_by(Device.enrolled_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_pending_devices(db: AsyncSession) -> List[Device]:
        """Get all devices awaiting approval"""
        return await DeviceService.get_devices_by_status(db, status="pending")
    
    @staticmethod
    async def get_all_devices(
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> List[Device]:
        """Get all devices with optional status filter"""
        query = select(Device).options(selectinload(Device.user))
        
        if status_filter:
            query = query.where(Device.status == status_filter)
        
        query = query.order_by(Device.enrolled_at.desc()).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_devices_by_user(db: AsyncSession, user_id: int) -> List[Device]:
        """Get all devices for a specific user"""
        result = await db.execute(
            select(Device)
            .where(Device.user_id == user_id)
            .order_by(Device.enrolled_at.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def approve_device(
        db: AsyncSession,
        device: Device,
        user_id: int
    ) -> Device:
        """
        Approve device enrollment and link to user
        Called after admin approves and user is created
        """
        device.status = "active"
        device.is_enrolled = True
        device.user_id = user_id
        
        await db.commit()
        await db.refresh(device)
        
        logger.info(f"Device {device.device_unique_id} approved and linked to user {user_id}")
        return device
    
    @staticmethod
    async def reject_device(
        db: AsyncSession,
        device: Device,
        rejection_reason: Optional[str] = None
    ) -> Device:
        """Reject device enrollment"""
        device.status = "rejected"
        device.is_enrolled = False
        device.is_active = False
        
        # Store rejection reason in posture_data if provided
        if rejection_reason:
            device.posture_data = device.posture_data or {}
            device.posture_data["rejection_reason"] = rejection_reason
        
        await db.commit()
        await db.refresh(device)
        
        logger.info(f"Device {device.device_unique_id} rejected")
        return device
    
    @staticmethod
    async def assign_device_to_user(
        db: AsyncSession,
        device: Device,
        user_id: int
    ) -> Device:
        """Assign device to existing user"""
        device.user_id = user_id
        device.status = "active"
        device.is_enrolled = True
        
        await db.commit()
        await db.refresh(device)
        
        logger.info(f"Device {device.device_unique_id} assigned to user {user_id}")
        return device
    
    @staticmethod
    async def update_device(
        db: AsyncSession,
        device: Device,
        update_data: DeviceUpdate
    ) -> Device:
        """Update device information"""
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for key, value in update_dict.items():
            setattr(device, key, value)
        
        await db.commit()
        await db.refresh(device)
        return device
    
    @staticmethod
    async def update_device_posture(
        db: AsyncSession,
        device: Device,
        posture_data: Dict[str, Any]
    ) -> Device:
        """Update device posture data"""
        device.posture_data = posture_data
        device.last_posture_check = datetime.now(timezone.utc)
        device.last_seen_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(device)
        return device
    
    @staticmethod
    async def update_compliance_status(
        db: AsyncSession,
        device: Device,
        is_compliant: bool
    ) -> Device:
        """Update device compliance status"""
        device.is_compliant = is_compliant
        
        await db.commit()
        await db.refresh(device)
        return device
    
    @staticmethod
    async def deactivate_device(db: AsyncSession, device: Device) -> Device:
        """Deactivate device"""
        device.is_active = False
        device.status = "inactive"
        
        await db.commit()
        await db.refresh(device)
        
        logger.info(f"Device {device.device_unique_id} deactivated")
        return device
    
    @staticmethod
    async def delete_device(db: AsyncSession, device: Device) -> bool:
        """Permanently delete device"""
        device_id = device.device_unique_id
        await db.delete(device)
        await db.commit()
        
        logger.info(f"Device {device_id} deleted")
        return True
