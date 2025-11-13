# services/user_service.py

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from datetime import datetime, timezone

class UserService:
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user from Keycloak sync"""
        user = User(**user_data.model_dump())
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_keycloak_id(db: AsyncSession, keycloak_id: str) -> Optional[User]:
        """Get user by Keycloak ID"""
        result = await db.execute(select(User).where(User.keycloak_id == keycloak_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_users(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = False
    ) -> List[User]:
        """Get all users with pagination"""
        query = select(User)
        if active_only:
            query = query.where(User.is_active == True)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_last_login(db: AsyncSession, user_id: int) -> Optional[User]:
        """Update user's last login timestamp"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        user.last_login = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def deactivate_user(db: AsyncSession, user_id: int) -> Optional[User]:
        """Deactivate a user"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """Delete a user (hard delete)"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        await db.delete(user)
        await db.commit()
        return True
