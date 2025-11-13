# services/device_service.py

from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate
from datetime import datetime, timezone

class DeviceService:
    @staticmethod
    async def create_device(db: AsyncSession, device_data: DeviceCreate) -> Device:
        """Create a new device"""
        device = Device(**device_data.model_dump())
        device.is_enrolled = True
        device.enrolled_at = datetime.now(timezone.utc)
        db.add(device)
        await db.commit()
        await db.refresh(device)
        return device

    @staticmethod
    async def get_device_by_id(db: AsyncSession, device_id: int) -> Optional[Device]:
        """Get device by ID"""
        result = await db.execute(select(Device).where(Device.id == device_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_device_by_unique_id(db: AsyncSession, device_unique_id: str) -> Optional[Device]:
        """Get device by unique ID (TPM fingerprint)"""
        result = await db.execute(select(Device).where(Device.device_unique_id == device_unique_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_devices_by_user(
        db: AsyncSession, 
        user_id: int,
        active_only: bool = False
    ) -> List[Device]:
        """Get all devices for a user"""
        query = select(Device).where(Device.user_id == user_id)
        if active_only:
            query = query.where(Device.is_active == True)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_all_devices(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        compliant_only: bool = False
    ) -> List[Device]:
        """Get all devices with pagination"""
        query = select(Device)
        if compliant_only:
            query = query.where(Device.is_compliant == True)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_device(db: AsyncSession, device_id: int, device_data: DeviceUpdate) -> Optional[Device]:
        """Update device information"""
        device = await DeviceService.get_device_by_id(db, device_id)
        if not device:
            return None
        
        update_data = device_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)
        
        device.last_seen_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(device)
        return device

    @staticmethod
    async def update_compliance_status(
        db: AsyncSession,
        device_id: int,
        is_compliant: bool,
        posture_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Device]:
        """Update device compliance status"""
        device = await DeviceService.get_device_by_id(db, device_id)
        if not device:
            return None
        
        device.is_compliant = is_compliant
        device.last_posture_check = datetime.now(timezone.utc)
        device.last_seen_at = datetime.now(timezone.utc)
        
        if posture_data:
            device.posture_data = posture_data
        
        await db.commit()
        await db.refresh(device)
        return device

    @staticmethod
    async def deactivate_device(db: AsyncSession, device_id: int) -> Optional[Device]:
        """Deactivate a device"""
        device = await DeviceService.get_device_by_id(db, device_id)
        if not device:
            return None
        
        device.is_active = False
        device.last_seen_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(device)
        return device

    @staticmethod
    async def delete_device(db: AsyncSession, device_id: int) -> bool:
        """Delete a device (hard delete)"""
        device = await DeviceService.get_device_by_id(db, device_id)
        if not device:
            return False
        
        await db.delete(device)
        await db.commit()
        return True
