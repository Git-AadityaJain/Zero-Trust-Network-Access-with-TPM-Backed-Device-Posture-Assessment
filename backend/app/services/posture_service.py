# services/posture_service.py

from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.posture_history import PostureHistory
from app.models.device import Device
from app.schemas.posture import PostureHistoryCreate
from datetime import datetime, timezone

class PostureService:
    @staticmethod
    async def create_posture_record(
        db: AsyncSession,
        posture_data: PostureHistoryCreate
    ) -> PostureHistory:
        """Create a new posture history record"""
        record = PostureHistory(**posture_data.model_dump())
        record.checked_at = datetime.now(timezone.utc)
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def get_posture_history(
        db: AsyncSession,
        device_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[PostureHistory]:
        """Get posture history for a device"""
        query = (
            select(PostureHistory)
            .where(PostureHistory.device_id == device_id)
            .order_by(PostureHistory.checked_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_latest_posture(db: AsyncSession, device_id: int) -> Optional[PostureHistory]:
        """Get the latest posture record for a device"""
        query = (
            select(PostureHistory)
            .where(PostureHistory.device_id == device_id)
            .order_by(PostureHistory.checked_at.desc())
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def evaluate_compliance(posture_data: Dict[str, Any]) -> tuple[bool, int, List[str]]:
        """
        Evaluate device compliance based on posture data
        Returns: (is_compliant, compliance_score, violations)
        """
        violations = []
        score = 100
        
        # Check antivirus status
        if not posture_data.get("antivirus_enabled"):
            violations.append("Antivirus not enabled")
            score -= 30
        
        # Check firewall status
        if not posture_data.get("firewall_enabled"):
            violations.append("Firewall not enabled")
            score -= 25
        
        # Check disk encryption
        if not posture_data.get("disk_encrypted"):
            violations.append("Disk encryption not enabled")
            score -= 25
        
        # Check OS updates
        if posture_data.get("pending_updates", 0) > 10:
            violations.append(f"{posture_data['pending_updates']} pending updates")
            score -= 10
        
        # Check screen lock
        if not posture_data.get("screen_lock_enabled"):
            violations.append("Screen lock not enabled")
            score -= 10
        
        is_compliant = score >= 70  # Compliance threshold
        
        return is_compliant, max(0, score), violations
