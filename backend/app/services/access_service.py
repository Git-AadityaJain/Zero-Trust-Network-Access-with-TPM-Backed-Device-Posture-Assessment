# services/access_service.py

from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.access_log import AccessLog
from app.schemas.access import AccessLogCreate
from datetime import datetime

class AccessService:
    @staticmethod
    async def create_access_log(db: AsyncSession, access_data: AccessLogCreate) -> AccessLog:
        """Create a new access log entry"""
        log = AccessLog(**access_data.model_dump())
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def log_access(
        db: AsyncSession,
        device_id: Optional[int],
        resource_accessed: str,
        access_type: str,
        access_granted: bool,
        denial_reason: Optional[str] = None,
        policy_id: Optional[int] = None,
        policy_name: Optional[str] = None,
        source_ip: Optional[str] = None,
        destination_ip: Optional[str] = None,
        request_metadata: Optional[Dict[str, Any]] = None
    ) -> AccessLog:
        """Convenience method to log an access attempt"""
        access_data = AccessLogCreate(
            device_id=device_id,
            resource_accessed=resource_accessed,
            access_type=access_type,
            access_granted=access_granted,
            denial_reason=denial_reason,
            policy_id=policy_id,
            policy_name=policy_name,
            source_ip=source_ip,
            destination_ip=destination_ip,
            request_metadata=request_metadata
        )
        return await AccessService.create_access_log(db, access_data)

    @staticmethod
    async def get_access_logs(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        device_id: Optional[int] = None,
        access_granted: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AccessLog]:
        """Get access logs with filters"""
        from app.models.device import Device
        from sqlalchemy.orm import selectinload
        
        query = select(AccessLog).options(selectinload(AccessLog.device))
        
        if device_id:
            query = query.where(AccessLog.device_id == device_id)
        
        if access_granted is not None:
            query = query.where(AccessLog.access_granted == access_granted)
        
        if start_date:
            query = query.where(AccessLog.accessed_at >= start_date)
        
        if end_date:
            query = query.where(AccessLog.accessed_at <= end_date)
        
        query = query.order_by(AccessLog.accessed_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
