# services/audit_service.py

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogCreate
from datetime import datetime

class AuditService:
    @staticmethod
    async def create_audit_log(db: AsyncSession, audit_data: AuditLogCreate) -> AuditLog:
        """Create a new audit log entry"""
        log = AuditLog(**audit_data.model_dump())
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def log_event(
        db: AsyncSession,
        event_type: str,
        action: str,
        status: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Convenience method to log an event"""
        audit_data = AuditLogCreate(
            user_id=user_id,
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return await AuditService.create_audit_log(db, audit_data)

    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: Optional[int] = None,
        action: str = "",
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Convenience method to log an action with details"""
        # Determine event_type from action if not provided
        event_type = "general"
        if action.startswith("user_"):
            event_type = "user_management"
        elif action.startswith("device_"):
            event_type = "device_management"
        elif action.startswith("policy_"):
            event_type = "policy_management"
        elif action.startswith("enrollment_"):
            event_type = "enrollment_code"
        
        audit_data = AuditLogCreate(
            user_id=user_id,
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            description=f"{action} on {resource_type or 'resource'}" if resource_type else action,
            status="success",
            event_metadata=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return await AuditService.create_audit_log(db, audit_data)

    @staticmethod
    async def get_audit_logs(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLog]:
        """Get audit logs with filters"""
        query = select(AuditLog)
        
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        
        if event_type:
            query = query.where(AuditLog.event_type == event_type)
        
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)
        
        query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
