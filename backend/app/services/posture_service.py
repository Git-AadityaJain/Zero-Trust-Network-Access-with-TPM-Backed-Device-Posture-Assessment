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
    def evaluate_compliance(posture_data: Dict[str, Any]) -> tuple[bool, int, List[str]]:
        """
        Evaluate device compliance based on posture data.
        Returns: (is_compliant, compliance_score, violations)
        
        Note: The posture_data structure from DPA is nested:
        - antivirus: {"installed": bool, "running": bool, "product_name": str}
        - firewall: {"firewall_enabled": bool, "firewall_profile": str}
        - disk_encryption: {"encryption_enabled": bool, "encryption_method": str}
        """
        import logging
        logger = logging.getLogger(__name__)
        
        violations = []
        score = 100
        
        # Extract nested data structures
        antivirus = posture_data.get("antivirus", {})
        firewall = posture_data.get("firewall", {})
        disk_encryption = posture_data.get("disk_encryption", {})
        screen_lock = posture_data.get("screen_lock", {})
        
        # Debug logging
        logger.info(f"Evaluating compliance - Antivirus: {antivirus}, Firewall: {firewall}, Disk Encryption: {disk_encryption}, Screen Lock: {screen_lock}")
        
        # Check antivirus status (must be installed AND running)
        antivirus_enabled = antivirus.get("installed", False) and antivirus.get("running", False)
        logger.info(f"Antivirus check - installed: {antivirus.get('installed')}, running: {antivirus.get('running')}, enabled: {antivirus_enabled}")
        if not antivirus_enabled:
            violations.append("Antivirus not enabled")
            score -= 30
        
        # Check firewall status
        firewall_enabled = firewall.get("firewall_enabled", False)
        logger.info(f"Firewall check - firewall_enabled: {firewall_enabled}")
        if not firewall_enabled:
            violations.append("Firewall not enabled")
            score -= 25
        
        # Check disk encryption
        disk_encrypted = disk_encryption.get("encryption_enabled", False)
        logger.info(f"Disk encryption check - encryption_enabled: {disk_encrypted}")
        if not disk_encrypted:
            violations.append("Disk encryption not enabled")
            score -= 25
        
        # Check OS updates (if present in os_info)
        os_info = posture_data.get("os_info", {})
        pending_updates = os_info.get("pending_updates", 0)
        if pending_updates > 10:
            violations.append(f"{pending_updates} pending updates")
            score -= 10
        
        # Check screen lock (from screen_lock dict)
        screen_lock_enabled = screen_lock.get("screen_lock_enabled", False)
        logger.info(f"Screen lock check - screen_lock_enabled: {screen_lock_enabled}")
        if not screen_lock_enabled:
            violations.append("Screen lock not enabled")
            score -= 10
        
        is_compliant = score >= 70  # Compliance threshold (70% or higher is compliant)
        
        logger.info(f"Final compliance evaluation - Compliant: {is_compliant}, Score: {score}%, Violations: {len(violations)}")
        
        return is_compliant, max(0, score), violations
