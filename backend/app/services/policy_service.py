# services/policy_service.py

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.policy import Policy
from app.schemas.policy import PolicyCreate, PolicyUpdate
from datetime import datetime, timezone

class PolicyService:
    @staticmethod
    async def create_policy(db: AsyncSession, policy_data: PolicyCreate) -> Policy:
        """Create a new policy"""
        policy = Policy(**policy_data.model_dump())
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        return policy

    @staticmethod
    async def get_policy_by_id(db: AsyncSession, policy_id: int) -> Optional[Policy]:
        """Get policy by ID"""
        result = await db.execute(select(Policy).where(Policy.id == policy_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_policy_by_name(db: AsyncSession, name: str) -> Optional[Policy]:
        """Get policy by name"""
        result = await db.execute(select(Policy).where(Policy.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_policies(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        policy_type: Optional[str] = None
    ) -> List[Policy]:
        """Get all policies with optional filters"""
        query = select(Policy)
        
        if active_only:
            query = query.where(Policy.is_active == True)
        
        if policy_type:
            query = query.where(Policy.policy_type == policy_type)
        
        query = query.order_by(Policy.priority.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_policy(
        db: AsyncSession,
        policy_id: int,
        policy_data: PolicyUpdate
    ) -> Optional[Policy]:
        """Update a policy"""
        policy = await PolicyService.get_policy_by_id(db, policy_id)
        if not policy:
            return None
        
        update_data = policy_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(policy, field, value)
        
        policy.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(policy)
        return policy

    @staticmethod
    async def delete_policy(db: AsyncSession, policy_id: int) -> bool:
        """Delete a policy"""
        policy = await PolicyService.get_policy_by_id(db, policy_id)
        if not policy:
            return False
        
        await db.delete(policy)
        await db.commit()
        return True
