# services/enrollment_service.py

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enrollment_code import EnrollmentCode
from app.schemas.enrollment import EnrollmentCodeCreate
from datetime import datetime, timezone
import secrets
import string

class EnrollmentService:
    @staticmethod
    def generate_code(length: int = 32) -> str:
        """Generate a secure random enrollment code"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    async def create_enrollment_code(
        db: AsyncSession,
        code_data: EnrollmentCodeCreate
    ) -> EnrollmentCode:
        """Create a new enrollment code"""
        code = EnrollmentCode(
            code=EnrollmentService.generate_code(),
            **code_data.model_dump()
        )
        db.add(code)
        await db.commit()
        await db.refresh(code)
        return code

    @staticmethod
    async def get_code_by_value(db: AsyncSession, code_value: str) -> Optional[EnrollmentCode]:
        """Get enrollment code by value"""
        result = await db.execute(
            select(EnrollmentCode).where(EnrollmentCode.code == code_value)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def validate_code(db: AsyncSession, code_value: str) -> tuple[bool, Optional[str]]:
        """Validate an enrollment code and return (is_valid, error_message)"""
        code = await EnrollmentService.get_code_by_value(db, code_value)
        
        if not code:
            return False, "Invalid enrollment code"
        
        if not code.is_active:
            return False, "Enrollment code is inactive"
        
        if code.is_expired:
            return False, "Enrollment code has expired"
        
        # Use timezone-aware datetime comparison
        if code.expires_at and code.expires_at < datetime.now(timezone.utc):
            code.is_expired = True
            await db.commit()
            return False, "Enrollment code has expired"
        
        if code.current_uses >= code.max_uses:
            return False, "Enrollment code usage limit reached"
        
        return True, None

    @staticmethod
    async def use_code(db: AsyncSession, code_value: str) -> Optional[EnrollmentCode]:
        """Mark an enrollment code as used"""
        code = await EnrollmentService.get_code_by_value(db, code_value)
        if not code:
            return None
        
        code.current_uses += 1
        code.last_used_at = datetime.now(timezone.utc)
        
        # Auto-expire if max uses reached
        if code.current_uses >= code.max_uses:
            code.is_active = False
        
        await db.commit()
        await db.refresh(code)
        return code

    @staticmethod
    async def get_all_codes(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> List[EnrollmentCode]:
        """Get all enrollment codes"""
        query = select(EnrollmentCode)
        if active_only:
            query = query.where(EnrollmentCode.is_active == True, EnrollmentCode.is_expired == False)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def deactivate_code(db: AsyncSession, code_id: int) -> Optional[EnrollmentCode]:
        """Deactivate an enrollment code"""
        result = await db.execute(select(EnrollmentCode).where(EnrollmentCode.id == code_id))
        code = result.scalar_one_or_none()
        
        if not code:
            return None
        
        code.is_active = False
        await db.commit()
        await db.refresh(code)
        return code
