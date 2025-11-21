# app/services/user_service.py

from typing import Optional, List
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management operations"""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user"""
        user = User(**user_data.model_dump())
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"User created: {user.username} (ID: {user.id})")
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
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(select(User).where(User.email == email))
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
        
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: int,
        user_update: UserUpdate
    ) -> Optional[User]:
        """Update user information"""
        user = await UserService.get_user_by_id(db, user_id)
        
        if not user:
            return None
        
        update_data = user_update.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(user, key, value)
        
        user.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(user)
        logger.info(f"User updated: {user.username} (ID: {user.id})")
        return user
    
    @staticmethod
    async def update_last_login(db: AsyncSession, user_id: int) -> bool:
        """Update user's last login timestamp"""
        user = await UserService.get_user_by_id(db, user_id)
        
        if not user:
            return False
        
        user.last_login = datetime.now(timezone.utc)
        await db.commit()
        return True
    
    @staticmethod
    async def deactivate_user(db: AsyncSession, user_id: int) -> Optional[User]:
        """Deactivate user account"""
        user = await UserService.get_user_by_id(db, user_id)
        
        if not user:
            return None
        
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(user)
        logger.info(f"User deactivated: {user.username} (ID: {user.id})")
        return user
    
    @staticmethod
    async def activate_user(db: AsyncSession, user_id: int) -> Optional[User]:
        """Activate user account"""
        user = await UserService.get_user_by_id(db, user_id)
        
        if not user:
            return None
        
        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(user)
        logger.info(f"User activated: {user.username} (ID: {user.id})")
        return user
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """Permanently delete user"""
        user = await UserService.get_user_by_id(db, user_id)
        
        if not user:
            return False
        
        username = user.username
        await db.delete(user)
        await db.commit()
        logger.info(f"User deleted: {username} (ID: {user_id})")
        return True
    
    @staticmethod
    async def search_users(
        db: AsyncSession,
        search_term: str,
        limit: int = 50
    ) -> List[User]:
        """Search users by username or email"""
        search_pattern = f"%{search_term}%"
        
        result = await db.execute(
            select(User)
            .where(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern)
                )
            )
            .limit(limit)
        )
        return list(result.scalars().all())
